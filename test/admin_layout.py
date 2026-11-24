# このファイルは test/ にある。python3 test/<名前>.py で動かす（リポジトリの一番上で）
import os, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
INDEX = 'file://' + os.path.join(ROOT, 'index.html')
OUT = os.path.join(HERE, 'out') + '/'; os.makedirs(OUT, exist_ok=True)
MOCK_PATH = os.path.join(HERE, 'mock-supabase.js')
_exe = glob.glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome'); LAUNCH = dict(executable_path=_exe[0]) if _exe else {}
from playwright.sync_api import sync_playwright
MOCK=open(MOCK_PATH).read()
O=OUT
with sync_playwright() as p:
    b=p.chromium.launch(**LAUNCH)
    for scheme in ['light','dark']:
        pg=b.new_page(viewport={'width':390,'height':844},color_scheme=scheme);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=MOCK,content_type='application/javascript'))
        pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
        pg.goto(INDEX);pg.wait_for_timeout(500)
        pg.click('nav.tabs button[data-tab=admin]');pg.wait_for_timeout(200);pg.screenshot(path=O+f'adm_{scheme}.png',full_page=True)
        for bid in ['addM','addP','addS','menuSort']: print(bid,pg.locator('#'+bid).count(),end=' ')
        pg.click('#addM');print('| addM opens:',pg.inner_text('#form h3'),errs)
    b.close()
