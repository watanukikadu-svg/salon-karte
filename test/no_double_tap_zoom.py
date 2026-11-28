# 2回すばやくたたいても画面が拡大されない設定（touch-action: manipulation）が、写真の拡大画面のボタンにも効いているか
# python3 test/no_double_tap_zoom.py（リポジトリの一番上で）
import os, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_exe = glob.glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome'); LAUNCH = dict(executable_path=_exe[0]) if _exe else {}
from playwright.sync_api import sync_playwright
MOCK = open(os.path.join(HERE, 'mock-supabase.js')).read()
with sync_playwright() as p:
    b = p.chromium.launch(**LAUNCH); pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase-js@*/**', lambda r: r.fulfill(body=MOCK, content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.goto('file://' + os.path.join(ROOT, 'index.html')); pg.wait_for_timeout(500)
    ng = []
    for sel in ['body', '#lb', '#lb [data-lb]', 'nav.tabs button', '#view']:
        v = pg.evaluate(f"(()=>{{const e=document.querySelector({sel!r});return e?getComputedStyle(e).touchAction:'なし'}})()")
        print(sel, v)
        if v != 'manipulation': ng.append(sel)
    print('errs', errs); b.close()
    if ng or errs: raise SystemExit('NG: ' + ', '.join(ng))
    print('すべてOK')
