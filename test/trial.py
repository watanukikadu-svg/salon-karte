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
S=OUT
def setup(p, pre=''):
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=pre+MOCK,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    calls=[]
    def fn(r):
        body=json.loads(r.request.post_data); calls.append(body)
        resp={'ok':True,'salon_code':body.get('salon_code'),'login_id':'owner'}
        r.fulfill(status=200,body=json.dumps(resp),content_type='application/json')
    pg.route('**/functions/v1/**',fn)
    pg.goto(INDEX);pg.wait_for_timeout(500)
    return b,pg,errs,calls
with sync_playwright() as p:
    # 初めて：はじめるボタン
    b,pg,errs,calls=setup(p,'window.__startSignedOut=true;')
    print('start visible',pg.locator('#start').is_visible(),'login hidden',not pg.locator('#loginForm').is_visible())
    pg.screenshot(path=S+'start.png')
    pg.click('#startBtn');pg.wait_for_timeout(600)
    print('calls',calls,'app',pg.locator('#app').is_visible(),'trialbar',pg.locator('.trialbar').count())
    pg.click('nav.tabs button[data-tab=admin]');pg.wait_for_timeout(200)
    print('logout btn',pg.locator('#logout').count(),'trial card',pg.locator('.carte.trial').count())
    pg.screenshot(path=S+'admin.png',full_page=True)
    pg.click('#addS');pg.wait_for_timeout(200);print('addS->reg',pg.inner_text('#form h3'))
    pg.fill('#r1','STAY GOLD');print('code auto',pg.input_value('#r2'));pg.fill('#r3','password123')
    pg.evaluate('window.__anon=false');pg.click('#form button[type=submit]');pg.wait_for_timeout(700)
    print('reg call',calls[-1]);print('after: logout',pg.locator('#logout').count(),'trial card',pg.locator('.carte.trial').count())
    print('errs',errs);b.close()
    # 残り20日：お知らせバー
    b,pg,errs,calls=setup(p,"window.__anon=true;")
    pg.evaluate("()=>{const d=new Date();d.setMonth(d.getMonth()-6);d.setDate(d.getDate()+20);__db.salons[0].created_at=d.toISOString()}");pg.click('nav.tabs button[data-tab=admin]');pg.click('#reload');pg.wait_for_timeout(300);pg.click('nav.tabs button[data-tab=cust]');pg.wait_for_timeout(200)
    print('bar:',pg.inner_text('.trialbar'))
    pg.screenshot(path=S+'bar.png')
    # 期限切れ
    pg.evaluate("()=>{const d=new Date();d.setMonth(d.getMonth()-7);__db.salons[0].created_at=d.toISOString()}");pg.click('nav.tabs button[data-tab=admin]');pg.click('#reload');pg.wait_for_timeout(300)
    print('expired title',pg.inner_text('#ttl'),'nav hidden',not pg.locator('nav.tabs').is_visible())
    pg.screenshot(path=S+'expired.png')
    pg.click('#regBtn');print('sheet',pg.inner_text('#form h3'))
    print('errs',errs);b.close()
    # 登録済みの人：ログイン画面
    b,pg,errs,calls=setup(p,"window.__startSignedOut=true;localStorage.setItem('salon-code','test');")
    print('returning: login visible',pg.locator('#loginForm').is_visible(),pg.input_value('#lcode'));print('errs',errs);b.close()
