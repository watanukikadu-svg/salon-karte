# テスト

画面（`index.html`）を、本物の Supabase の代わりに `mock-supabase.js`（ブラウザの中だけで動く偽物）につないで、Playwright で操作して確かめる。

## 動かし方（リポジトリの一番上で）
```
pip install playwright        # 最初の一度だけ（ブラウザは環境に入っているものを使う）
python3 test/run_all.py       # 全部まとめて
python3 test/walk_in.py       # 1つだけ
```
画面の写真は `test/out/` に保存される（git には入れない）。

## 一覧
| ファイル | 確かめること |
|---|---|
| run.py | ログイン・施術記録・店販と在庫・写真・予約・売上・スタッフ追加・顧客追加（全体の流れ） |
| trial.py | 「はじめる」で登録なしで使う・登録・6か月のお知らせと期限切れ |
| create_salon.py | 運営者のお店づくり（入力4つ・お店コードの自動入力） |
| owner_login.py | オーナーはスタッフID空欄でログインできる |
| login_logout.py | 管理タブのログイン・ログアウト（お試し中の確認） |
| delete_account.py | アカウントの消去（「消去」と入力） |
| booking_picker.py | 予約のお客様選び（検索・カタカナ・電話・500人） |
| booked_badge.py | 「予約あり」の印 |
| due_soon.py / due_soon_none.py | 来店周期から、そろそろ来店しそうなお客様（いる・いない） |
| booking_menus.py | 予約のメニュー複数・合計 |
| same_name_menus.py | 同じ名前のメニュー（カット4800円・4000円）を取りちがえない |
| booking_items.py | 予約の店販 |
| booking_avatar.py | 予約カードの顔アイコン |
| timeline.py | 予約のタイムライン表示 |
| visit_links_booking.py | カルテから施術を記録 → その日の予約につながる・消すと戻る |
| walk_in.py | 予約なしで来店 → 予約の画面に残る・直す・消す |
| upcoming.py | カルテの「これからの予約」 |
| carte_buttons.py | カルテのボタンの並び |
| new_customer_button.py | 顧客一覧の「＋ 新しいお客様」が右下にいつも出る（100人・スマホとPC） |
| delete_buttons.py | 顧客・来店履歴の削除が編集画面にある・1日平均 |
| photo_limit.py / photo_limit_existing.py | 写真は9枚まで・お知らせの文 |
| sort_menus.py / sort_products_staff.py / sort_single.py | 並び替え |
| admin_layout.py | 管理タブの枠（明るい・暗い） |
| swipe_back.py | 左端からのスワイプ・ブラウザの戻る |
| legal_links.py | 利用規約・プライバシーポリシーへのリンク |
| screenshots.py | 見本データを入れて主な画面の写真をとる（確かめるだけ） |
