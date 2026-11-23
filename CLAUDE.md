# サロンカルテ：Claude への指示

## 返事のしかた（必ず守る）
- ユーザーへの返事は、毎回かならず **日本語** で書く。英語で書かない。
- 専門用語は使わず、やさしい言葉で書く。
- 何を直したか・どう使うかを、短く箇条書きでまとめる。

## このアプリについて
- 公開先：https://watanukikadu-svg.github.io/salon-karte/ （GitHub Pages。main に push すると反映）
- 画面は `index.html` 1ファイル。サーバー側は Supabase（プロジェクト `lnawjlzsgaeziovfxkvk`）と Edge Function `supabase/functions/salon-admin`。
- テストは `test/mock-supabase.js`（Supabase の偽物）と Playwright で行う。
