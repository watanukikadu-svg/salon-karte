# App Store Connect のサブスクリプション（月額・年額）に入れる「審査用のスクリーンショット」を作る。
# アプリの「有料プラン」の画面（iPhone アプリのとき）を、6.7インチ（1290×2796）で撮る。見本のデータは架空。
# 使い方（リポジトリの一番上で）：python3 store/make_iap_screenshot.py → store/iap/paywall.png
import os, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
MOCK = open(os.path.join(ROOT, 'test', 'mock-supabase.js')).read()
NATIVE = """window.Capacitor={isNativePlatform:()=>true,getPlatform:()=>'ios'};
window.__salonCreated=(()=>{const d=new Date();d.setMonth(d.getMonth()-7);return d.toISOString()})();
window.RCPurchases={configure:async()=>{},logIn:async()=>{},restorePurchases:async()=>({}),purchasePackage:async()=>({}),
 getOfferings:async()=>({current:{availablePackages:[{packageType:'MONTHLY',product:{title:'月額プラン',priceString:'¥600'}},{packageType:'ANNUAL',product:{title:'年額プラン',priceString:'¥6,000'}}]}})};"""
_exe = glob.glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome'); LAUNCH = dict(executable_path=_exe[0]) if _exe else {}
with sync_playwright() as p:
    b = p.chromium.launch(**LAUNCH)
    pg = b.new_page(viewport={'width': 430, 'height': 932}, device_scale_factor=3)
    pg.route('**/supabase-js@*/**', lambda r: r.fulfill(body=NATIVE + MOCK, content_type='application/javascript'))
    pg.goto('file://' + os.path.join(ROOT, 'index.html')); pg.wait_for_timeout(1500)
    pg.evaluate("document.fonts && document.fonts.ready")
    pg.click('#planBtn'); pg.wait_for_timeout(800)
    pg.evaluate("document.querySelector('#sub').textContent='サロン見本・オーナー'")  # 見本の名前にする
    out = os.path.join(ROOT, 'store', 'iap', 'paywall.png')
    pg.screenshot(path=out); b.close()
    print('作りました:', out)
