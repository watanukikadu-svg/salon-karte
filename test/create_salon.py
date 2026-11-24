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
with sync_playwright() as p:
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body='window.__startSignedOut=true;'+MOCK,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    calls=[]
    def fn(r): calls.append((r.request.headers.get('x-admin-key'),json.loads(r.request.post_data))); r.fulfill(status=200,body='{"ok":true}',content_type='application/json')
    pg.route('**/functions/v1/**',fn)
    pg.goto(INDEX);pg.wait_for_timeout(500)
    pg.click('#toLogin');pg.click('#toAdmin');pg.fill('#ak','secretkey');pg.type('#an','STAY GOLD')
    print('auto code:',pg.input_value('#ac'))
    pg.screenshot(path=OUT+'form.png')
    pg.fill('#aop','password123');pg.click('#admin button[type=submit]');pg.wait_for_timeout(500)
    print('call:',calls)
    print('login shown',pg.locator('#loginForm').is_visible(),pg.input_value('#lcode'),pg.input_value('#lid'),pg.inner_text('#lmsg'))
    # 手入力したコードは上書きしない
    pg.click('#toAdmin');pg.fill('#ac','my-shop');pg.type('#an','ABC');print('kept:',pg.input_value('#ac'))
    print('errs',errs);b.close()
