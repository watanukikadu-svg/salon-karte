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
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=MOCK,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.goto(INDEX);pg.wait_for_timeout(500)
    names=lambda: pg.eval_on_selector_all('.adm >> nth=0','e=>[...e[0].querySelectorAll("b")].map(x=>x.textContent)')
    db=lambda: pg.evaluate("__db.menus.slice().sort((a,b)=>a.sort-b.sort).map(m=>m.name)")
    pg.click('nav.tabs button[data-tab=admin]');print('before',names(),db())
    pg.click('#menuSort');pg.wait_for_timeout(100);pg.screenshot(path=O+'ms.png')
    pg.click('[data-mmv="m2:-1"]');pg.wait_for_timeout(200);pg.click('[data-mmv="m2:-1"]');pg.wait_for_timeout(300)
    print('after',names(),'saved',db(),'top up disabled',pg.locator('[data-mmv="m2:-1"]').is_disabled())
    pg.click('#menuSort');print('done mode edit buttons',pg.locator('[data-em]').count())
    pg.click('nav.tabs button[data-tab=book]');pg.click('#addB');print('booking menu order',pg.eval_on_selector('#bmrows select','e=>[...e.options].map(o=>o.value)'))
    pg.click('#cancel');pg.click('nav.tabs button[data-tab=admin]');pg.click('#reload');pg.wait_for_timeout(300);print('after reload',names(),errs)
    b.close()
