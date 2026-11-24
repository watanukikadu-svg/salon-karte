# このファイルは test/ にある。python3 test/<名前>.py で動かす（リポジトリの一番上で）
import os, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
INDEX = 'file://' + os.path.join(ROOT, 'index.html')
OUT = os.path.join(HERE, 'out') + '/'; os.makedirs(OUT, exist_ok=True)
MOCK_PATH = os.path.join(HERE, 'mock-supabase.js')
_exe = glob.glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome'); LAUNCH = dict(executable_path=_exe[0]) if _exe else {}
import json
from playwright.sync_api import sync_playwright
MOCK=open(MOCK_PATH).read()
def setup(p, signed_out=False):
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m: m.type=='error' and errs.append(m.text))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=('window.__startSignedOut=true;' if signed_out else '')+"window.__planUntil='2099-01-01T00:00:00Z';"+MOCK,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    calls=[]
    def fn(r):
        calls.append(json.loads(r.request.post_data or '{}'))
        r.fulfill(status=200,body=json.dumps({'ok':True,'staff':{'id':'new','display_name':'新人'}}),content_type='application/json',headers={'Access-Control-Allow-Origin':'*'})
    pg.route('**/functions/v1/**',fn)
    pg.goto(INDEX);pg.wait_for_timeout(500)
    return b,pg,errs,calls
with sync_playwright() as p:
    # ログイン画面
    b,pg,errs,calls=setup(p,True)
    print('start visible',pg.locator('#start').is_visible())
    pg.click('#toLogin')
    pg.fill('#lcode','Test');pg.fill('#lid','Owner');pg.fill('#lpw','wrong');pg.click('#loginForm button[type=submit]');pg.wait_for_timeout(300)
    print('bad pw msg:',pg.inner_text('#lmsg'))
    pg.fill('#lpw','password1');pg.click('#loginForm button[type=submit]');pg.wait_for_timeout(500)
    print('email:',pg.evaluate('window.__lastEmail'),'app visible',pg.locator('#app').is_visible(), pg.inner_text('#sub'))
    pg.screenshot(path=OUT+'p1.png')
    # 施術記録
    pg.click('.list li button >> nth=0');pg.click('#addV')
    pg.click('#addMr');pg.select_option('#mrows select >> nth=1','2')
    pg.click('#addPr');pg.select_option('#prows select',index=1);pg.fill('#prows input','2')
    pg.set_input_files('#v6',[OUT+'p1.png']*3)
    pg.click('#form button[type=submit]');pg.wait_for_timeout(1500)
    print('visit:',pg.inner_text('.visit >> nth=0').replace('\n',' | '))
    print('stock',pg.evaluate('__db.products[0].stock'),'photos',pg.evaluate('__db.visit_photos.length'),'uploads',len(pg.evaluate('window.__uploads')))
    # 編集：写真1枚外す・店販を1に
    pg.click('[data-ev]');pg.click('.pk button >> nth=0');pg.fill('#prows input','1');pg.click('#form button[type=submit]');pg.wait_for_timeout(1000)
    print('after edit stock',pg.evaluate('__db.products[0].stock'),'photos',pg.evaluate('__db.visit_photos.length'),'removed',pg.evaluate('window.__removed'))
    # 予約→来店完了
    pg.click('nav.tabs button[data-tab=book]');pg.click('#addB');pg.fill('#b1q','さとう');pg.click('#b1res .pk-row >> nth=0');pg.click('#form button[type=submit]');pg.wait_for_timeout(500)
    pg.screenshot(path=OUT+'p2.png')
    pg.click('[data-open]');pg.click('#addV');pg.click('#form button[type=submit]');pg.wait_for_timeout(800)
    print('booking status',pg.evaluate('__db.bookings[0].status'),'visits',pg.evaluate('__db.visits.length'))
    # 売上
    pg.click('nav.tabs button[data-tab=sales]');pg.wait_for_timeout(200);print('sales',pg.inner_text('.big .v'));pg.screenshot(path=OUT+'p3.png',full_page=True)
    # 管理：スタッフ追加
    pg.click('nav.tabs button[data-tab=admin]');pg.click('#addS');pg.fill('#s1','新人');pg.fill('#s2','shinjin');pg.fill('#s3','abcdefgh');pg.check('input[name=can_view_sales]');pg.click('#form button[type=submit]');pg.wait_for_timeout(700)
    print('fn call',calls[-1])
    pg.screenshot(path=OUT+'p4.png',full_page=True)
    # 顧客追加
    pg.click('nav.tabs button[data-tab=cust]');pg.click('#addC');pg.fill('#f1','高橋 花');pg.fill('#f2','たかはし はな');pg.set_input_files('#f8',OUT+'p1.png');pg.click('#form button[type=submit]');pg.wait_for_timeout(800)
    print('customers',pg.evaluate('__db.customers.length'),'face',pg.evaluate('__db.customers[1].face_path'))
    print('errs',errs);b.close()
    # スタッフ権限（売上なし）
    b,pg,errs,calls=setup(p)
    pg.evaluate("""()=>{}""")
    b.close()
