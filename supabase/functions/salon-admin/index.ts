// サロン顧客管理：ログイン用アカウントの管理
//  - create_salon : 新しいお店とオーナーを作る（運営者だけ。ADMIN_KEY が必要）
//  - create_staff : スタッフを追加する（オーナー、または「スタッフ管理」権限のある人）
//  - set_password : スタッフのパスワードを再設定する（同上）
//  - set_active   : スタッフの利用を止める／再開する（同上）
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

async function caller(req: Request) {
  const token = (req.headers.get("Authorization") ?? "").replace(/^Bearer\s+/i, "");
  if (!token) return null;
  const { data, error } = await admin.auth.getUser(token);
  if (error || !data.user) return null;
  const { data: me } = await admin.from("staff").select("*").eq("user_id", data.user.id).eq("active", true).maybeSingle();
  return me;
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
      if (!CODE_RE.test(code)) return fail("お店コードは半角英小文字・数字・ハイフンで3〜30文字");
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
        if (body.seed_menus !== false) {
          await admin.from("menus").insert(DEFAULT_MENUS.map(([name, price, duration_min], i) => ({ salon_id: salon.id, name, price, duration_min, sort: i })));
        }
      } catch (e) {
        await admin.from("salons").delete().eq("id", salon.id);
        return fail((e as Error).message);
      }
      return json({ ok: true, salon_id: salon.id, salon_code: code });
    }

    // ---------- ここから先はログイン中のオーナー／スタッフ管理者 ----------
    const me = await caller(req);
    if (!me) return fail("ログインしてください", 401);
    if (!canManage(me)) return fail("スタッフを管理する権限がありません", 403);
    const { data: salon } = await admin.from("salons").select("id, code").eq("id", me.salon_id).single();

    if (action === "create_staff") {
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
