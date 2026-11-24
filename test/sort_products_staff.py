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
SEED="(()=>{const d=window.__db;d.products.push({id:'p2',salon_id:'s1',name:'ワックス',price:1800,stock:4,sort:1,active:true,created_at:'2'},{id:'p3',salon_id:'s1',name:'オイル',price:2500,stock:2,sort:2,active:true,created_at:'3'})})();"
def run(pre):
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=pre+MOCK+SEED,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.goto(INDEX);pg.wait_for_timeout(500);pg.click('nav.tabs button[data-tab=admin]');return b,pg,errs
with sync_playwright() as p:
    b,pg,errs=run('')
    pg.click('#prodSort');pg.click('[data-pmv="p3:-1"]');pg.wait_for_timeout(200);pg.click('[data-pmv="p3:-1"]');pg.wait_for_timeout(300)
    print('products saved',pg.evaluate("__db.products.slice().sort((a,b)=>a.sort-b.sort).map(x=>x.name)"));pg.click('#prodSort')
    pg.click('#staffSort');pg.click('[data-smv="st2:-1"]');pg.wait_for_timeout(300)
    print('staff saved',pg.evaluate("__db.staff.slice().sort((a,b)=>a.sort-b.sort).map(x=>x.display_name)"))
    pg.screenshot(path=O+'ssort.png',full_page=True);pg.click('#staffSort')
    pg.click('nav.tabs button[data-tab=book]');pg.click('#addB');print('stylist options',pg.eval_on_selector('#stylist','e=>[...e.options].map(o=>o.text)'),errs);b.close()
    b,pg,errs=run("window.__uid='u2';")
    print('staff (non-owner) sort buttons:',pg.locator('#staffSort').count(),pg.locator('#menuSort').count(),errs);b.close()
