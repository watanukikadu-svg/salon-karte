// サロン顧客管理：ログイン用アカウントの管理
//  - create_salon : 新しいお店とオーナーを作る（運営者だけ。ADMIN_KEY が必要）
//  - create_staff : スタッフを追加する（オーナー、または「スタッフ管理」権限のある人）
//  - set_password : スタッフのパスワードを再設定する（同上）
//  - set_active   : スタッフの利用を止める／再開する（同上）
//  - start_trial  : 登録なしのお試しを始める（匿名ログインした人が、自分のお店を自動で作る）
//  - register     : お試し中のオーナーが、お店コード＋パスワードを登録して本登録にする
//  - delete_account : アカウントを消す（オーナー＝お店ごと全部、スタッフ＝自分のログインだけ）
// ログイン自体はアプリから「お店コード＋スタッフID＋パスワード」で行う。
// 内部では loginEmail() で作ったメールアドレス形式のIDを使う（メールは送られない）。
import { createClient } from "npm:@supabase/supabase-js@2";

const URL = Deno.env.get("SUPABASE_URL")!;
const SECRET = (() => {
  try {
    const keys = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}");
    if (keys.default) return keys.default as string;
  } catch { /* 古い形式の鍵を使う */ }
  return Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
})();
const admin = createClient(URL, SECRET, { auth: { persistSession: false, autoRefreshToken: false } });

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-admin-key",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });
const fail = (msg: string, status = 400) => json({ error: msg }, status);

const CODE_RE = /^[a-z0-9-]{3,30}$/;
const LOGIN_RE = /^[a-z0-9._-]{2,30}$/;
export const loginEmail = (code: string, login: string) => `${login}.${code}@staff.example.com`;
const okPassword = (p: unknown) => typeof p === "string" && p.length >= 8 && p.length <= 72;

const PERMS = ["can_view_sales", "can_edit_master", "can_delete_customers", "can_manage_staff"] as const;
const DEFAULT_MENUS = [
  ["カット", 4800, 60], ["カット＋カラー", 11000, 120], ["カラー", 7700, 90], ["パーマ", 12100, 120],
  ["縮毛矯正", 18700, 180], ["トリートメント", 4400, 30], ["ヘッドスパ", 5500, 45],
];

function safeEqual(a: string, b: string) {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

async function authUser(req: Request) {
  const token = (req.headers.get("Authorization") ?? "").replace(/^Bearer\s+/i, "");
  if (!token) return null;
  const { data, error } = await admin.auth.getUser(token);
  if (error || !data.user) return null;
  return data.user;
}
async function staffOf(uid: string) {
  const { data: me } = await admin.from("staff").select("*").eq("user_id", uid).eq("active", true).maybeSingle();
  return me;
}
// お試し中＝匿名ログインのまま（メール形式のIDがまだ付いていない）
const isTrial = (u: { is_anonymous?: boolean; email?: string }) => !!u.is_anonymous && !u.email;
const randCode = () => "t-" + Array.from(crypto.getRandomValues(new Uint8Array(10)), (b) => "abcdefghijkmnpqrstuvwxyz23456789"[b % 32]).join("");
async function seedMenus(salonId: string) {
  await admin.from("menus").insert(DEFAULT_MENUS.map(([name, price, duration_min], i) => ({ salon_id: salonId, name, price, duration_min, sort: i })));
}
// お店の写真フォルダ（salon-photos/<お店のID>/...）を中身ごと消す
async function removeSalonFiles(salonId: string) {
  const bucket = admin.storage.from("salon-photos");
  const files: string[] = [];
  const walk = async (dir: string) => {
    for (let off = 0; ; off += 1000) {
      const { data } = await bucket.list(dir, { limit: 1000, offset: off });
      if (!data?.length) break;
      for (const f of data) { const full = dir + "/" + f.name; if (f.id) files.push(full); else await walk(full); }
      if (data.length < 1000) break;
    }
  };
  await walk(salonId);
  for (let i = 0; i < files.length; i += 100) await bucket.remove(files.slice(i, i + 100));
}
const canManage = (me: any) => me && (me.role === "owner" || me.can_manage_staff);

async function createLogin(code: string, login: string, password: string) {
  const { data, error } = await admin.auth.admin.createUser({
    email: loginEmail(code, login), password, email_confirm: true,
    app_metadata: { salon_code: code, login_id: login },
  });
  if (error) throw new Error(error.message.includes("already") ? "このIDはすでに使われています" : "アカウントを作れませんでした");
  return data.user!.id;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return fail("POST only", 405);
  let body: any;
  try { body = await req.json(); } catch { return fail("JSONで送ってください"); }
  const action = body?.action;

  try {
    // ---------- 新しいお店（運営者のみ） ----------
    if (action === "create_salon") {
      const key = Deno.env.get("ADMIN_KEY") ?? "";
      if (!key || !safeEqual(req.headers.get("x-admin-key") ?? "", key)) return fail("権限がありません", 403);
      const code = String(body.salon_code ?? "").toLowerCase();
      const login = String(body.owner_login_id ?? "").toLowerCase();
      if (!CODE_RE.test(code) || code.startsWith("t-")) return fail("お店コードは半角英小文字・数字・ハイフンで3〜30文字");
      if (!LOGIN_RE.test(login)) return fail("スタッフIDは半角英小文字・数字・._- で2〜30文字");
      if (!body.salon_name || !body.owner_name) return fail("お店の名前とオーナーの名前を入れてください");
      if (!okPassword(body.owner_password)) return fail("パスワードは8文字以上");

      const { data: salon, error: e1 } = await admin.from("salons").insert({ code, name: body.salon_name }).select().single();
      if (e1) return fail(e1.code === "23505" ? "このお店コードはすでに使われています" : "お店を作れませんでした");
      try {
        const uid = await createLogin(code, login, body.owner_password);
        const { error: e2 } = await admin.from("staff").insert({
          salon_id: salon.id, user_id: uid, login_id: login, display_name: body.owner_name, role: "owner",
          can_view_sales: true, can_edit_master: true, can_delete_customers: true, can_manage_staff: true,
        });
        if (e2) { await admin.auth.admin.deleteUser(uid); throw new Error("オーナーを登録できませんでした"); }
        if (body.seed_menus !== false) await seedMenus(salon.id);
      } catch (e) {
        await admin.from("salons").delete().eq("id", salon.id);
        return fail((e as Error).message);
      }
      return json({ ok: true, salon_id: salon.id, salon_code: code });
    }

    const user = await authUser(req);
    if (!user) return fail("ログインしてください", 401);

    // ---------- 登録なしのお試しを始める ----------
    if (action === "start_trial") {
      if (!isTrial(user)) return fail("お試しは登録前の人だけが使えます", 403);
      const already = await staffOf(user.id);
      if (already) return json({ ok: true, salon_id: already.salon_id });
      const name = String(body.salon_name ?? "").trim().slice(0, 60) || "マイサロン";
      let salon: any = null;
      for (let i = 0; i < 3 && !salon; i++) {
        const { data, error } = await admin.from("salons").insert({ code: randCode(), name }).select().single();
        if (!error) salon = data; else if (error.code !== "23505") break;
      }
      if (!salon) return fail("お店を作れませんでした", 500);
      const { error: e2 } = await admin.from("staff").insert({
        salon_id: salon.id, user_id: user.id, login_id: "owner", display_name: "オーナー", role: "owner",
        can_view_sales: true, can_edit_master: true, can_delete_customers: true, can_manage_staff: true,
      });
      if (e2) { await admin.from("salons").delete().eq("id", salon.id); return fail("お店を作れませんでした", 500); }
      await seedMenus(salon.id);
      return json({ ok: true, salon_id: salon.id });
    }

    // ---------- ここから先はログイン中のオーナー／スタッフ管理者 ----------
    const me = await staffOf(user.id);
    if (!me) return fail("ログインしてください", 401);

    // ---------- お試しから本登録へ（お店コード＋パスワードを決める） ----------
    if (action === "register") {
      if (me.role !== "owner") return fail("登録はオーナーだけができます", 403);
      if (!isTrial(user)) return fail("このお店はもう登録済みです");
      const code = String(body.salon_code ?? "").trim().toLowerCase();
      const name = String(body.salon_name ?? "").trim().slice(0, 60);
      if (!CODE_RE.test(code) || code.startsWith("t-")) return fail("お店コードは半角英小文字・数字・ハイフンで3〜30文字");
      if (!okPassword(body.password)) return fail("パスワードは8文字以上");
      const { data: old } = await admin.from("salons").select("code, name").eq("id", me.salon_id).single();
      const { error: e1 } = await admin.from("salons").update({ code, ...(name ? { name } : {}) }).eq("id", me.salon_id);
      if (e1) return fail(e1.code === "23505" ? "このお店コードはすでに使われています" : "登録できませんでした");
      const { error: e2 } = await admin.auth.admin.updateUserById(user.id, {
        email: loginEmail(code, me.login_id), password: body.password, email_confirm: true,
        app_metadata: { salon_code: code, login_id: me.login_id },
      });
      if (e2) {
        await admin.from("salons").update({ code: old!.code, name: old!.name }).eq("id", me.salon_id);
        return fail(e2.message.includes("already") ? "このお店コードはすでに使われています" : "登録できませんでした");
      }
      return json({ ok: true, salon_code: code, login_id: me.login_id });
    }

    // ---------- アカウントを消す ----------
    if (action === "delete_account") {
      if (body.confirm !== "削除") return fail("確認のため「削除」と入力してください");
      if (me.role === "owner") {
        // お店ごと消す：写真 → お店（顧客・来店・予約などは一緒に消える） → スタッフ全員のログイン
        const { data: members } = await admin.from("staff").select("user_id").eq("salon_id", me.salon_id);
        await removeSalonFiles(me.salon_id);
        const { error } = await admin.from("salons").delete().eq("id", me.salon_id);
        if (error) return fail("削除できませんでした。時間をおいてもう一度お試しください", 500);
        for (const m of members ?? []) if (m.user_id) await admin.auth.admin.deleteUser(m.user_id);
        return json({ ok: true, deleted: "salon" });
      }
      // スタッフは自分のログインだけ消す（来店記録の「担当」の名前は残す）
      await admin.from("staff").update({ active: false }).eq("id", me.id);
      const { error } = await admin.auth.admin.deleteUser(user.id);
      if (error) return fail("削除できませんでした。時間をおいてもう一度お試しください", 500);
      return json({ ok: true, deleted: "account" });
    }

    if (!canManage(me)) return fail("スタッフを管理する権限がありません", 403);
    const { data: salon } = await admin.from("salons").select("id, code").eq("id", me.salon_id).single();

    if (action === "create_staff") {
      if (isTrial(user)) return fail("スタッフを追加するには、先にお店の登録をしてください", 403);
      const login = String(body.login_id ?? "").toLowerCase();
      if (!LOGIN_RE.test(login)) return fail("スタッフIDは半角英小文字・数字・._- で2〜30文字");
      if (!body.display_name) return fail("名前を入れてください");
      if (!okPassword(body.password)) return fail("パスワードは8文字以上");
      const { data: dup } = await admin.from("staff").select("id").eq("salon_id", me.salon_id).eq("login_id", login).maybeSingle();
      if (dup) return fail("このIDはすでに使われています");
      const perms: Record<string, boolean> = {};
      // 自分が持っていない権限は人に渡せない（オーナーは全部渡せる）
      for (const p of PERMS) perms[p] = !!body[p] && (me.role === "owner" || !!me[p]);
      const uid = await createLogin(salon!.code, login, body.password);
      const { data: row, error } = await admin.from("staff").insert({
        salon_id: me.salon_id, user_id: uid, login_id: login, display_name: body.display_name,
        role: "staff", is_stylist: body.is_stylist !== false, ...perms,
      }).select("id, login_id, display_name").single();
      if (error) { await admin.auth.admin.deleteUser(uid); return fail("スタッフを登録できませんでした"); }
      return json({ ok: true, staff: row });
    }

    if (action === "set_password" || action === "set_active") {
      const { data: target } = await admin.from("staff").select("*").eq("id", body.staff_id).eq("salon_id", me.salon_id).maybeSingle();
      if (!target) return fail("スタッフが見つかりません", 404);
      if (target.role === "owner" && me.role !== "owner") return fail("オーナーの設定はオーナーだけが変えられます", 403);
      if (action === "set_password") {
        if (!okPassword(body.password)) return fail("パスワードは8文字以上");
        if (!target.user_id) return fail("このスタッフにはログインがありません");
        const { error } = await admin.auth.admin.updateUserById(target.user_id, { password: body.password });
        if (error) return fail("パスワードを変えられませんでした");
        return json({ ok: true });
      }
      const active = !!body.active;
      if (!active && target.id === me.id) return fail("自分自身は止められません");
      await admin.from("staff").update({ active }).eq("id", target.id);
      if (target.user_id) {
        // 止めたスタッフはログインもできなくする
        await admin.auth.admin.updateUserById(target.user_id, { ban_duration: active ? "none" : "876000h" });
      }
      return json({ ok: true });
    }

    return fail("不明な操作です");
  } catch (e) {
    return fail((e as Error).message || "エラーが起きました", 500);
  }
});
