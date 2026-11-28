# 有料プラン：6か月の無料期間・スタッフ追加のときの案内、Web と iPhone アプリの申し込み、課金済み、スタッフ
# python3 test/plan.py（リポジトリの一番上で）
import os, glob, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
INDEX = 'file://' + os.path.join(ROOT, 'index.html')
OUT = os.path.join(HERE, 'out') + '/'; os.makedirs(OUT, exist_ok=True)
_exe = glob.glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome'); LAUNCH = dict(executable_path=_exe[0]) if _exe else {}
from playwright.sync_api import sync_playwright
MOCK = open(os.path.join(HERE, 'mock-supabase.js')).read()
FUTURE = '2099-01-01T00:00:00Z'
fails = []
def check(name, ok, extra=''):
    print(('OK  ' if ok else 'NG  ') + name, extra)
    if not ok: fails.append(name)

def setup(p, pre='', sync=None):
    b = p.chromium.launch(**LAUNCH); pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase-js@*/**', lambda r: r.fulfill(body=pre + MOCK, content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    calls = []
    def fn(r):
        body = json.loads(r.request.post_data); calls.append(body)
        resp = sync or {'ok': True, 'plan_until': None, 'plan_store': None, 'management_url': None}
        r.fulfill(status=200, body=json.dumps(resp), content_type='application/json')
    pg.route('**/functions/v1/**', fn)
    pg.goto(INDEX); pg.wait_for_timeout(500)
    return b, pg, errs, calls

EXPIRED = "window.__salonCreated=(()=>{const d=new Date();d.setMonth(d.getMonth()-7);return d.toISOString()})();"
SOON = "window.__salonCreated=(()=>{const d=new Date();d.setMonth(d.getMonth()-6);d.setDate(d.getDate()+20);return d.toISOString()})();"
NATIVE = """window.Capacitor={isNativePlatform:()=>true,getPlatform:()=>'ios'};window.__pay={iosKey:'appl_test'};
window.__rc=[];window.RCPurchases=(o=>new Proxy(o,{get:(t,k)=>k in t?t[k]:(()=>Promise.reject(new Error(String(k)+" is not implemented")))}))({
 configure:async o=>{__rc.push(['configure',o.appUserID])},logIn:async o=>{__rc.push(['logIn',o.appUserID])},
 getOfferings:async()=>({current:{availablePackages:[{packageType:'MONTHLY',product:{title:'月額',priceString:'¥600'}},{packageType:'ANNUAL',product:{title:'年額',priceString:'¥6,000'}}]}}),
 purchasePackage:async o=>{__rc.push(['buy',o.aPackage.packageType]);__db.salons[0].plan_until='2099-01-01T00:00:00Z';__db.salons[0].plan_store='app_store';return {}},
 restorePurchases:async()=>{__rc.push(['restore']);return {}}});"""

with sync_playwright() as p:
    # 1) Web：無料期間中・課金なし → 管理タブにプラン、スタッフ追加で有料プランの案内
    b, pg, errs, calls = setup(p, "window.__pay={webLink:'https://pay.rev.cat/abc/'};", sync={'ok': True, 'plan_until': FUTURE, 'plan_store': 'rc_billing', 'management_url': 'https://billing.example/manage'})
    pg.click('nav.tabs button[data-tab=admin]'); pg.wait_for_timeout(200)
    acc = pg.inner_text('.acc')
    check('管理タブにプラン（無料期間）', '無料期間' in acc, acc.replace('\n', ' '))
    pg.click('#addS'); pg.wait_for_timeout(200)
    form = pg.inner_text('#form')
    check('スタッフ追加 → 有料プランの案内', pg.inner_text('#form h3') == '有料プラン' and 'スタッフを追加するには' in form)
    check('Web の値段（600円・6,000円）', '600円' in form and '6,000円' in form)
    href = pg.get_attribute('#plWeb', 'href')
    check('申し込みリンクにお店のID', href == 'https://pay.rev.cat/abc/s1', href)
    check('特定商取引法の表記へのリンク', pg.locator('#form a[href="tokushoho.html"]').count() == 1)
    pg.screenshot(path=OUT + 'plan_web.png', full_page=True)
    # 払った（サーバーが記録した）→ 確認する
    pg.evaluate(f"__db.salons[0].plan_until='{FUTURE}';__db.salons[0].plan_store='rc_billing'")
    pg.click('#plCheck'); pg.wait_for_timeout(600)
    check('確認するで sync_plan を呼ぶ', calls and calls[-1].get('action') == 'sync_plan')
    check('お申し込み後はシートが閉じる', not pg.locator('#sheet.open').count())
    pg.click('#addS'); pg.wait_for_timeout(200)
    check('課金後はスタッフ追加の画面', pg.inner_text('#form h3') == 'スタッフを追加', pg.inner_text('#form h3'))
    check('エラーなし(1)', not errs, errs); b.close()

    # 2) Web：準備中（リンク未設定）
    b, pg, errs, calls = setup(p)
    pg.click('nav.tabs button[data-tab=admin]'); pg.click('#planBtn'); pg.wait_for_timeout(200)
    check('リンク未設定なら準備中', '準備中' in pg.inner_text('#form') and pg.locator('#plWeb').count() == 0)
    check('エラーなし(2)', not errs, errs); b.close()

    # 3) 残り20日：お知らせ
    b, pg, errs, calls = setup(p, SOON)
    bar = pg.inner_text('.trialbar') if pg.locator('.trialbar').count() else ''
    check('残り20日のお知らせ', '有料プランを見る' in bar and 'あと' in bar, bar)
    check('エラーなし(3)', not errs, errs); b.close()

    # 4) 期限切れ・課金なし（オーナー）→ 有料プランの画面だけ。消去・ログアウトはできる
    b, pg, errs, calls = setup(p, EXPIRED)
    check('期限切れ：タイトル', pg.inner_text('#ttl') == '有料プラン', pg.inner_text('#ttl'))
    check('期限切れ：下のタブを隠す', not pg.locator('nav.tabs').is_visible())
    check('期限切れ：消去・ログアウトのボタン', pg.locator('#delAcc').count() == 1 and pg.locator('#logout').count() == 1)
    check('期限切れ：右下のボタンが出ない', pg.locator('.btn.fab').count() == 0 or not pg.locator('.btn.fab').is_visible())
    pg.screenshot(path=OUT + 'plan_expired.png', full_page=True)
    pg.click('#delAcc'); pg.wait_for_timeout(200)
    check('期限切れ：消去の画面が開く', 'お店とアカウントを消去' in pg.inner_text('#form h3'))
    check('エラーなし(4)', not errs, errs); b.close()

    # 5) 期限切れ・課金済み → ふつうに使える
    b, pg, errs, calls = setup(p, EXPIRED + f"window.__planUntil='{FUTURE}';window.__planStore='app_store';")
    check('課金済み：ふつうの画面', pg.inner_text('#ttl') == '顧客カルテ' and pg.locator('nav.tabs').is_visible())
    pg.click('nav.tabs button[data-tab=admin]'); pg.wait_for_timeout(200)
    check('課金済み：プランの表示', '有料プラン（2099年' in pg.inner_text('.acc'), pg.inner_text('.acc').replace('\n', ' '))
    pg.click('#planBtn'); pg.wait_for_timeout(200)
    f = pg.inner_text('#form')
    check('Web で App Store の契約を見る → iPhone の設定の案内', 'サブスクリプション' in f and pg.locator('#plWeb').count() == 0)
    check('申し込んだ人には「6か月」の話を出さない', '6か月' not in f and 'すべての機能が使えます' in f and '解約しない限り、自動で更新' in f, f.replace('\n',' ')[:200])
    pg.click('#form [type=submit]'); pg.wait_for_timeout(100)
    pg.click('#delAcc'); pg.wait_for_timeout(200)
    check('課金中に消去：解約の案内', '自動更新は、お店を消しても止まりません' in pg.inner_text('#form'))
    check('エラーなし(5)', not errs, errs); b.close()

    # 6) 期限が過ぎた記録があれば、読み込みのあと RevenueCat に確かめ直す（自動更新されているかも）
    b, pg, errs, calls = setup(p, EXPIRED + "window.__planUntil='2020-01-01T00:00:00Z';", sync={'ok': True, 'plan_until': FUTURE, 'plan_store': 'app_store'})
    pg.wait_for_timeout(500)
    check('期限すぎ → 確かめ直す', any(c.get('action') == 'sync_plan' for c in calls))
    check('確かめ直して更新されていれば使える', pg.inner_text('#ttl') == '顧客カルテ', pg.inner_text('#ttl'))
    check('エラーなし(6)', not errs, errs); b.close()

    # 7) スタッフ（オーナーでない）・期限切れ → オーナーに頼む案内
    b, pg, errs, calls = setup(p, EXPIRED + "window.__uid='u2';")
    check('スタッフ：期限切れの画面', pg.inner_text('#ttl') == '有料プラン')
    pg.click('#planBtn'); pg.wait_for_timeout(200)
    check('スタッフ：オーナーに伝える案内', 'オーナー' in pg.inner_text('#form') and pg.locator('#plWeb').count() == 0)
    check('スタッフ：消去は自分のアカウント', pg.inner_text('#delAcc') == '自分のアカウントを消去する')
    check('エラーなし(7)', not errs, errs); b.close()

    # 8) iPhone アプリ：Apple の課金。Web の値段・リンクは出さない
    b, pg, errs, calls = setup(p, EXPIRED + NATIVE, sync={'ok': True, 'plan_until': FUTURE, 'plan_store': 'app_store'})
    pg.click('#planBtn'); pg.wait_for_timeout(400)
    f = pg.inner_text('#form')
    check('アプリ：Apple の値段を出す', '¥600' in f and '¥6,000' in f, f.replace('\n', ' ')[:200])
    check('アプリ：Web の値段・リンク・特商法を出さない', '特定商取引法' not in f and pg.locator('#plWeb').count() == 0 and pg.locator('#form a[href="tokushoho.html"]').count() == 0)
    check('アプリ：自動更新の説明・復元・EULA', '自動で更新' in f and pg.locator('#plRestore').count() == 1 and pg.locator('#form a[href*="stdeula"]').count() == 1)
    check('アプリ：お客様ID＝お店のID', pg.evaluate('__rc')[0] == ['configure', 's1'], pg.evaluate('__rc'))
    pg.screenshot(path=OUT + 'plan_app.png', full_page=True)
    pg.click('[data-pk="0"]'); pg.wait_for_timeout(700)
    check('アプリ：月額を買う', ['buy', 'MONTHLY'] in pg.evaluate('__rc'))
    check('アプリ：買ったあと sync_plan', any(c.get('action') == 'sync_plan' for c in calls))
    check('アプリ：買ったあとふつうに使える', pg.inner_text('#ttl') == '顧客カルテ' and not pg.locator('#sheet.open').count(), pg.inner_text('#ttl'))
    check('エラーなし(8)', not errs, errs); b.close()

    # 9) アプリ：購入を復元（見つからない）
    b, pg, errs, calls = setup(p, EXPIRED + NATIVE)
    pg.click('#planBtn'); pg.wait_for_timeout(300); pg.click('#plRestore'); pg.wait_for_timeout(500)
    check('アプリ：復元を呼ぶ', ['restore'] in pg.evaluate('__rc'))
    check('アプリ：見つからないお知らせ', '見つかりませんでした' in pg.inner_text('#toastMsg'), pg.inner_text('#toastMsg'))
    check('エラーなし(9)', not errs, errs); b.close()

    # 9b) アプリ：買えたがサーバーの確認がまだ → 失敗とは言わない
    b, pg, errs, calls = setup(p, EXPIRED + NATIVE.replace("__db.salons[0].plan_until='2099-01-01T00:00:00Z';__db.salons[0].plan_store='app_store';", ''))
    pg.click('#planBtn'); pg.wait_for_timeout(300); pg.click('[data-pk="1"]'); pg.wait_for_timeout(500)
    check('アプリ：確認が遅れたら「受け付けました」', '受け付けました' in pg.inner_text('#toastMsg'), pg.inner_text('#toastMsg'))
    check('エラーなし(9b)', not errs, errs); b.close()

    # 9c) アプリ：Apple から返事がない → 時間切れで「もう一度読み込む」、押すと読み込める
    HANG = NATIVE.replace("window.__pay={iosKey:'appl_test'};", "window.__pay={iosKey:'appl_test',timeoutMs:400};").replace(
        "getOfferings:async()=>(", "getOfferings:async()=>{if(!window.__ok)return new Promise(()=>{});return (").replace(
        "priceString:'¥6,000'}}]}}),", "priceString:'¥6,000'}}]}})},")
    b, pg, errs, calls = setup(p, EXPIRED + HANG)
    pg.click('#planBtn'); pg.wait_for_timeout(900)
    f = pg.inner_text('#form')
    check('アプリ：時間切れで読み込み中のままにしない', '読み込んでいます' not in f and '読み込めませんでした' in f and '時間切れ（値段の読み込み' in f and pg.locator('#plRetry').count() == 1, f.replace('\n', ' ')[:120])
    pg.evaluate('window.__ok=true'); pg.click('#plRetry'); pg.wait_for_timeout(500)
    check('アプリ：もう一度読み込むで値段が出る', '¥600' in pg.inner_text('#form'))
    check('エラーなし(9c)', not errs, errs); b.close()

    # 11) 管理タブ：有料プランのボタン（未払いは目立つ色・課金済みはふつう）
    b, pg, errs, calls = setup(p)
    pg.click('nav.tabs button[data-tab=admin]'); pg.wait_for_timeout(200)
    check('未払い：有料プランを見る（目立つボタン）', pg.inner_text('#planBtn') == '有料プランを見る' and 'pri' in pg.get_attribute('#planBtn', 'class'))
    pg.locator('#planBtn').scroll_into_view_if_needed(); pg.screenshot(path=OUT + 'plan_admin.png')
    b.close()
    b, pg, errs, calls = setup(p, f"window.__planUntil='{FUTURE}';")
    pg.click('nav.tabs button[data-tab=admin]'); pg.wait_for_timeout(200)
    check('課金済み：有料プランの確認（ふつうのボタン）', pg.inner_text('#planBtn') == '有料プランの確認' and 'pri' not in pg.get_attribute('#planBtn', 'class'))
    check('エラーなし(11)', not errs, errs); b.close()

    # 9d) アプリ：Apple が「やめた」と返した → サーバーに確かめに行き、理由を画面に残す
    CANCEL = NATIVE.replace("purchasePackage:async o=>{", "purchasePackage:async o=>{const e=new Error('Purchase was cancelled.');e.code='1';e.userCancelled=true;throw e;")
    CANCEL = CANCEL.replace("configure:async o=>{", "setLogLevel:async()=>{},setLogHandler:cb=>{window.__log=cb},configure:async o=>{").replace(
        "purchasePackage:async o=>{const e", "purchasePackage:async o=>{__log&&__log({logLevel:'ERROR',message:'StoreKit test log'});const e")
    b, pg, errs, calls = setup(p, EXPIRED + CANCEL)
    pg.click('#planBtn'); pg.wait_for_timeout(300); pg.click('[data-pk="0"]'); pg.wait_for_timeout(500)
    f = pg.inner_text('#form')
    check('アプリ：やめた扱いでもサーバーに確かめる', any(c.get('action') == 'sync_plan' for c in calls))
    check('アプリ：原因調べ用の記録を出す', 'StoreKit test log' in f)
    check('アプリ：やめた扱いの理由を画面に残す', '完了していません' in f and 'Purchase was cancelled' in f, f.replace('\n', ' ')[-160:])
    check('エラーなし(9d)', not errs, errs); b.close()

    # 10) お試し（登録なし）で期限切れ → 先にお店の登録
    b, pg, errs, calls = setup(p, EXPIRED + "window.__anon=true;")
    check('登録なし・期限切れ：登録の画面', pg.inner_text('#ttl') == 'お店の登録')
    check('エラーなし(10)', not errs, errs); b.close()

print('\n' + ('すべてOK' if not fails else 'NG: ' + ', '.join(fails)))
if fails: raise SystemExit(1)
