// アプリ（iPhone・Android）に入れる画面を www/ にまとめる。
// サイト（GitHub Pages）は今までどおりリポジトリの index.html をそのまま使う。
// アプリでは Supabase の部品をネットから読まず、アプリの中に入れておく（通信が不安定でも起動できるように）。
import { cpSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";

const OUT = "www";
rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });
for (const f of ["privacy.html", "terms.html", "manifest.webmanifest"]) cpSync(f, `${OUT}/${f}`);
cpSync("icons", `${OUT}/icons`, { recursive: true });
cpSync("node_modules/@supabase/supabase-js/dist/umd/supabase.js", `${OUT}/supabase.js`);

const CDN = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.0/dist/umd/supabase.js"></script>';
let html = readFileSync("index.html", "utf8");
if (!html.includes(CDN)) throw new Error("index.html の Supabase の読み込み部分が見つかりません（バージョンを変えたら build.mjs も直す）");
html = html.replace(CDN, '<script src="supabase.js"></script>');
writeFileSync(`${OUT}/index.html`, html);
console.log("www/ を作りました");
