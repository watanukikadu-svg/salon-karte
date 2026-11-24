# このファイルは test/ にある。python3 test/<名前>.py で動かす（リポジトリの一番上で）
import os, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
INDEX = 'file://' + os.path.join(ROOT, 'index.html')
OUT = os.path.join(HERE, 'out') + '/'; os.makedirs(OUT, exist_ok=True)
MOCK_PATH = os.path.join(HERE, 'mock-supabase.js')
_exe = glob.glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome'); LAUNCH = dict(executable_path=_exe[0]) if _exe else {}
from playwright.sync_api import sync_playwright
S=OUT
MOCK=open(MOCK_PATH).read()
with sync_playwright() as p:
    b=p.chromium.launch(**LAUNCH)
    pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.goto(INDEX.replace('index.html','terms.html'));pg.screenshot(path=S+'tm.png',full_page=True)
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body='window.__startSignedOut=true;'+MOCK,content_type='application/javascript'))
    pg.goto(INDEX);pg.wait_for_timeout(500);pg.screenshot(path=S+'pp_start.png')
    print('links on start',pg.locator('#start a[href="privacy.html"]').count(),'login',pg.locator('#loginForm a[href="privacy.html"]').count(),errs);b.close()
