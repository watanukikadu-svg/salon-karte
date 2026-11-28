# 美容室カルテ：Claude への指示と引き継ぎメモ

## 返事のしかた（必ず守る）
- ユーザーへの返事は、毎回かならず **日本語** で書く。最初の一文字から最後まで日本語。英語で書かない（謝りの一文やビルドの報告も含めて）。
  - この約束を何度も破って、ユーザーを強く怒らせた。作業のあと、送る前に必ず「全部日本語か」を確かめる。
  - **作業の途中に出す短い一言**（「テストします」「画面を直します」など、道具を使う前後の文）も必ず日本語。ユーザーはスマホでそれも全部読んでいる。ここが英語になりやすいので特に気をつける。
- 専門用語は使わず、やさしい言葉で書く。
- 何を直したか・どう使うかを、短く箇条書きでまとめる。
- ユーザーは iPhone の Safari と TestFlight で確かめている。画面の見た目に敏感で、スクリーンショットで指示してくる。
- 意味があいまいなときは、作り始める前に短く確かめる（すれ違いでやり直しになったことがある）。

## アプリの概要
- 名前：**美容室カルテ**（App Store の名前も同じ。「サロンカルテ」は使われていたので変えた）
- 運営者：STAYGOLD（連絡先 watakadu@icloud.com。プライバシーポリシー・利用規約に載せている）
- 美容室向けの顧客カルテ・予約・売上・スタッフ管理。スマホ1台で使う前提。

## 置き場所と仕組み
- サイト：https://watanukikadu-svg.github.io/salon-karte/ （GitHub Pages。main に push すると1分ほどで反映）
- 画面は `index.html` 1ファイル（HTML・CSS・JavaScript がすべて入っている）。`privacy.html`（プライバシーポリシー）、`terms.html`（利用規約）、`manifest.webmanifest`、`icons/`。
- サーバー：Supabase（プロジェクト `lnawjlzsgaeziovfxkvk`、東京）
  - 表：salons, staff, menus, products, customers, visits, visit_menus, visit_items, visit_photos, bookings（すべて RLS あり。お店ごとに分ける）
  - 写真：ストレージ `salon-photos/<お店のID>/...`
  - Edge Function `supabase/functions/salon-admin/index.ts`（verify_jwt は false。中で自分で確かめる）
    - 動き：create_salon（運営者用・ADMIN_KEY が必要）、start_trial、register、create_staff、set_password、set_active、delete_account
    - 直したら Supabase の MCP（deploy_edge_function）で、ファイルの中身を丸ごと送ってデプロイする
  - あとから足したデータベースの変更は `supabase/migrations/` に控えがある（どれも本番に適用済み）
  - Supabase の設定で「Allow anonymous sign-ins」をオンにしてある（お試しに必要）
  - Supabase は今は無料プラン。本番でお客様のデータを預かる前に有料（バックアップあり）にするよう伝えてある

## アプリ（iPhone・Android）
- Capacitor で `index.html` を包んでいる。`npm run build`（`scripts/build.mjs`）で `www/` を作り、`npx cap sync` で ios/ android/ に入れる。`www/` は git に入れない。
- アプリでは Supabase の部品をネットからでなくアプリの中から読む（build.mjs が書きかえる）。
- アプリID：`com.watanukikadu.salonkarte`。App Store Connect のアプリ「美容室カルテ」。
- **iPhone 版の作り方**：GitHub Actions の「iPhone 版を App Store に送る」（`.github/workflows/ios-release.yml` と `fastlane/Fastfile`）。Mac は不要。
  - 動かし方：`gh api -X POST repos/watanukikadu-svg/salon-karte/actions/workflows/ios-release.yml/dispatches -f ref=main`
  - ビルド番号＝実行の番号。終わると TestFlight に届く（ユーザーは TestFlight の一番新しい番号を入れる）
  - 結果のログは `ci-logs` ブランチ（`git fetch --depth 1 origin ci-logs` → `git show origin/ci-logs:ios-ci.log`）
  - ときどき GitHub 側で「取り消し（cancelled）」になることがある。アプリの中身の問題ではない。次のビルドに変更は全部入る
  - GitHub の Secrets：APPLE_TEAM_ID, ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_P8（ユーザーが登録済み）
- **iPhone 専用・縦向きだけ**（TARGETED_DEVICE_FAMILY = 1。iPad 用の画面写真がいらないように）
- **App Store のページ**：GitHub Actions の「App Store の情報を送る」（`.github/workflows/store.yml`、Fastfile の `store`）。ubuntu で fastlane deliver を使う
  - 文：`fastlane/metadata/`（説明文・キーワード・サブタイトルなど）、審査の人へのメモ：`fastlane/review_information/`
  - 画面写真：`store/make_screenshots.py` で作る（6.9インチ 1320×2868、見本のデータはすべて架空）→ `store/screenshots/`
  - 動かし方：`gh api -X POST repos/watanukikadu-svg/salon-karte/actions/workflows/store.yml/dispatches -f ref=main -f 'inputs[version]=1.0.0' -f 'inputs[submit]=false'`（画面写真だけ：`-f 'inputs[only_screenshots]=true'`、審査に出す：`-f 'inputs[submit]=true' -f 'inputs[build]=番号'`）
  - 結果のログは `store-logs` ブランチ
  - 審査の連絡先（姓・名・電話番号）が App Store Connect に入っていないと、文を送る作業は「No data」などで止まる（画面写真だけなら送れる）
  - 価格・年齢制限・App のプライバシー・審査の連絡先は、ユーザーが App Store Connect で手で入れる
  - 配信は**中国本土を外している**（中国向けの特別な手続きが必要になるため）。審査に出すとき「きまりの手続きが済んでいない」と止められたら、配信する国を確かめる
- サポートのページ：`support.html`
- Android 版は作る仕組みはあるが出さない（Google Play の「テスター12人・14日」の決まりがあるため）。ANDROID_KEYSTORE_PASSWORD も今は登録していない。
- アイコン：紺の背景に金色のはさみ（ユーザーが ChatGPT で作った絵）。`icons/icon-1024.png` が元。

## これまでに決めた仕様（変えるときはユーザーに確かめる）
- **お試し**：最初の画面は「はじめる」だけ。押すと登録なし（匿名ログイン）で自分のお店が自動でできる。**6か月**は登録なしで使える（利用規約に「お試しの6か月は無料です。」）。残り30日からお知らせ、6か月をすぎると登録の画面だけになる。スタッフ追加・別の端末で使うにも登録が必要。
- **ログイン**：お店コード＋スタッフID＋個人パスワード。オーナーはスタッフIDを空欄でよい（中では owner）。辞めたスタッフは「利用を止める」。
- **お店の登録**：お店の名前・お店コード・パスワードの3つ。名前が英字ならお店コードを自動で入れる。
- **アカウントを消す**：管理タブの一番下。確認の言葉は「**消去**」（サーバーは前の「削除」も受け付ける）。オーナーはお店ごと全部、スタッフは自分のログインだけ。
- **最初のメニュー**：カット・カット＋カラー・カラー・パーマ・縮毛矯正（トリートメントとヘッドスパは入れない）。
- **メニュー**：同じ名前でも金額か時間がちがえば登録できる（例：カット4800円とカット4000円）。予約・施術記録ではメニューを名前ではなく id で選ぶ（予約は menu_ids も保存）。名前が同じものがあるときだけ選択肢に金額を出す。売上の「メニュー別」は名前でまとめる。
- **写真**：1回の来店につき**9枚**まで（サーバー側も9枚）。
- **予約を追加**：
  - お客様は検索して選ぶ（名前・ふりがな・カタカナ・電話の一部）。すでに予約がある人には「予約あり」の印。
  - 何も入れていないときは「来店周期から、そろそろ来店しそうなお客様」：目安の日（前回の来店＋周期）の**前後14日以内**で、**予約がない人**を近い順に最大6人。**いなければ何も出さない**。周期は来店の間隔の真ん中の値（7日未満は数えない、1回だけの人はお店全体の値）。今日より先の日付の来店は数えない。
  - メニューは複数入れられる（各行の右に金額）。店販（買う予定の商品）も入れられる（在庫は施術を記録したときだけ減る）。
- **予約と施術記録**：「来店完了」ボタンはない。カルテの「＋ 施術を記録」で、その日のまだ来店していない予約があれば自動でつながる（予約が「来店済み」に）。予約がない日に記録すると、その日時で「予約なしで来店」の予約を自動で作る（walk_in）。記録を消すと、walk_in の予約は消え、ふつうの予約は「まだ来店していない」に戻る。
- **売上**：施術記録だけから数える（予約は数えない）。
- **予約画面**：リスト／タイムライン（横が時間、縦がスタッフ）を切り替えられる。予約カードに顔アイコン。取消ボタンはカードの右端。
- **誕生日の入力**：カレンダーの小窓（iPhone で閉じにくい）は使わず、「年・月・日」の3つの選択。年は今年から1920年まで新しい順。すべて空なら未登録。
- **顧客一覧**：「＋ 新しいお客様」は画面右下（下のタブのすぐ上）にいつも出る丸いボタン。PCでは真ん中の列の右端にそろえる。
- **カルテ画面**：プロフィール → 「予約を入れる」（濃い青緑）→「＋ 施術を記録」（赤）→「これからの予約」→「来店履歴」。
- **管理タブ**：サロンメニュー・店販商品・スタッフ・アカウントをそれぞれ枠で囲む。メニュー・店販・スタッフは並び替えできる（スタッフはオーナーだけ）。ログイン・ログアウトのボタンあり（お試し中は、消える前に登録をすすめる）。
- **戻る**：左端から右へスワイプ、ブラウザの戻るで、写真の拡大 → 入力シート → カルテ詳細 の順に閉じる。

## テスト
- `test/mock-supabase.js`：ブラウザの中だけで動く Supabase の偽物（並び替えの order() は効かないので、読み直すと順番が元に戻って見える。本物では大丈夫）
- `test/*.py`：Playwright のテスト。`python3 test/run_all.py` で全部動かす（先に一度 `pip install playwright`）。くわしくは `test/README.md`
- 直したら、全部のテストを通してから push する。

## これから（ユーザーと話したが、まだやっていないこと）
- App Store への申請：2026年11月24日にビルド28（1.0.0）で出したが「2.1 情報が足りない」で戻された。iPhone で撮った画面の録画と、5つの質問の答え（`fastlane/review_information/notes.txt` に書いた）を求められた。11月25日に、録画とメモをつけて出し直した。**11月27日に審査に通った（デベロッパによるリリース待ち）**。自動で公開しない設定なので、通ったら App Store Connect で「このバージョンをリリース」を押してもらう。通らなかったら、App Review のメッセージを見て直して出し直す
- Supabase を有料プランにする（本番で使う前）
- 長く使われていないお試し店の掃除、お試し6か月の期限をサーバー側でも守る
- ほかの端末の変更をすぐ画面に出す（リアルタイム更新）
- 予約から見込める売上の表示
- **課金（1.1.0。ブランチ claude/upbeat-ride-hdgmuc で作成中。main にはまだ入れていない）**：値段 iPhone（Apple）月600円／年6000円、Web（カード）も月600円／年6000円（11/28 に500円から変更。手数料を考えて同じ値段にそろえた）。人数で値段は変えない。iPhone アプリの中で Web の申し込み・値段は案内しない（Apple の決まり）
  - しくみ：RevenueCat。お客様ID＝お店のID（salons.id）、権利（entitlement）の名前は `pro`。iPhone は `@revenuecat/purchases-capacitor`（build.mjs が esbuild で www/purchases.js にまとめ、window.RCPurchases で使う。Web 版には入らない）。Web は RevenueCat の Web Purchase Link（Stripe）に、お店のIDをつけて開く
  - 払ったかどうか：`salons.plan_until`（期限）・`plan_store`・`plan_checked_at`（migrations/salons_plan.sql。アプリからは書きかえられない）。Edge Function の `sync_plan`（RevenueCat の V1 API に聞いて書く）と webhook（body に event）で更新
  - 画面：使いはじめて6か月（salons.created_at から）すぎて未払い → 「有料プラン」の画面だけ（ログアウト・消去はできる）。スタッフ追加も未払いなら有料プランの案内。管理タブのアカウント欄に「プラン」と「有料プラン」ボタン。申し込みはオーナーだけ
  - index.html の `PAY`（iosKey＝RevenueCat の Apple 用公開キー appl_…、webLink＝Web Purchase Link）が空の間は「準備中」と出る
  - Supabase の Secrets（ユーザーがダッシュボードで入れる）：RC_SECRET_KEY（V1 の秘密の鍵）、RC_WEBHOOK_AUTH（webhook の Authorization の値）。PLAN_ENFORCE=1 でサーバーもスタッフ追加を止める（1.1.0 を出すときにオン）
  - サーバーの処理（sync_plan・webhook）と salons の欄は本番に入れ済み（今のアプリには影響なし）
  - 済んだ設定（11/24）：RevenueCat のアカウント・アプリ「美容室カルテ (App Store)」（アプリ内課金キー・App Store Connect API キー・Apple のサーバー通知 URL）、商品 salonkarte_pro_monthly（¥600）・salonkarte_pro_yearly（¥6,000）（グループ「有料プラン」）、権利 pro、Offering default（$rc_monthly・$rc_annual）、PAY.iosKey、Supabase の RC_SECRET_KEY・RC_WEBHOOK_AUTH、RevenueCat の webhook（テストで 200 を確認）
  - RevenueCat が自動で作った見本（Test Store の商品・権利「美容室カルテ_pro」）は使わない。消さずに置いてある
  - 注意：課金の部品（window.RCPurchases）は then も含めどんな名前にも反応するので、async 関数から返したり await したりすると永久に止まる（ビルド33までの「準備で時間切れ」の原因）。テストの偽物も同じ作り（Proxy）にしてある
  - 11/27：有料アプリ契約・銀行口座・納税フォーム（W-8BEN と米国外の証明書）はすべて有効。月額・年額とも Ready to Submit。年額プランは「審査用に追加」で提出物の下書きに入っている（1.1.0 と一緒に出す）
  - 11/28：**TestFlight（ビルド37）でお試しの支払いが成功**（STAYGOLD のお店。salons.plan_until・plan_store=app_store が入り、画面も有料プランに変わった）。TestFlight の月額は1日で1か月分が過ぎる。
    - 途中で「支払い画面が出ずにすぐ『やめた』（SKErrorDomain 2 / SKInternalErrorDomain 13）」になったが、**iPhone の再起動で直った**（アプリの不具合ではなかった）。同じことを言われたら、まず再起動をすすめる
    - そのとき試しに StoreKit 1 にしたが、元の既定（StoreKit 2）に戻した。**出す前にもう一度 TestFlight で支払いを確かめる**
  - サブスクリプションの審査用スクリーンショット：`store/make_iap_screenshot.py` → `store/iap/paywall.png`
  - tokushoho.html の運営責任者は「綿貫和也」（11/26 決定）
  - 出す前にやること：**PAY.debug を false にする（原因調べ用の記録を消す）**、PAY.webLink を入れる、App Store Connect の商品・App のプライバシー（購入履歴）、利用規約・プライバシーポリシーの改定日をそろえる、PLAN_ENFORCE=1、main に入れる
