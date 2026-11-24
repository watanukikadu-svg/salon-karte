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
SEED="(()=>{window.__db.products.push({id:'p2',salon_id:'s1',name:'トリートメント剤',price:2200,stock:5,sort:1,active:true,created_at:'2'})})();"
with sync_playwright() as p:
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=MOCK+SEED,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.goto(INDEX);pg.wait_for_timeout(500)
    pg.click('nav.tabs button[data-tab=book]');pg.click('#addB');pg.wait_for_timeout(200)
    pg.fill('#b1q','さとう');pg.click('#b1res .pk-row >> nth=0')
    pg.click('#addBp');pg.select_option('#bprows select >> nth=0','p1');pg.fill('#bprows input >> nth=0','2')
    pg.click('#addBp');pg.select_option('#bprows select >> nth=1','p2');pg.wait_for_timeout(100)
    print('sum:',pg.inner_text('#bpsum'));pg.locator('#bprows').scroll_into_view_if_needed();pg.screenshot(path=O+'bp.png')
    pg.click('#form button[type=submit]');pg.wait_for_timeout(400)
    bk=pg.evaluate('__db.bookings[__db.bookings.length-1]');print('saved items',bk['items'],'stock unchanged',pg.evaluate('__db.products[0].stock'))
    print('card:',pg.inner_text('.book li >> nth=0').replace('\n',' | '))
    # カルテから記録 → 店販が入っている
    pg.click('[data-open]');pg.click('#addV');pg.wait_for_timeout(200)
    print('visit prows:',pg.eval_on_selector_all('#prows .prw','e=>e.map(r=>r.querySelector("select").value+"×"+r.querySelector("input").value)'))
    pg.click('#form button[type=submit]');pg.wait_for_timeout(500)
    print('after record stock',pg.evaluate('__db.products.map(p=>p.name+":"+p.stock)'),'booking',pg.evaluate('__db.bookings[__db.bookings.length-1].status'))
    # 変更で開くと残っている
    print(errs);b.close()
