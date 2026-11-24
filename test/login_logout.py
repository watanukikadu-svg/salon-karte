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
def setup(p,pre):
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=pre+MOCK,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.goto(INDEX);pg.wait_for_timeout(500);return b,pg,errs
vis=lambda pg:{k:pg.locator(k).is_visible() for k in ['#app','#start','#loginForm']}
with sync_playwright() as p:
    # 登録済み
    b,pg,errs=setup(p,"localStorage.setItem('salon-code','test');")
    pg.click('nav.tabs button[data-tab=admin]');print('registered buttons:',pg.inner_text('#relogin'),'/',pg.inner_text('#logout'))
    pg.click('#logout');pg.wait_for_timeout(300);print('logout ->',vis(pg),pg.input_value('#lcode'))
    b.close()
    b,pg,errs=setup(p,"localStorage.setItem('salon-code','test');")
    pg.click('nav.tabs button[data-tab=admin]');pg.click('#relogin');pg.wait_for_timeout(300);print('relogin ->',vis(pg));b.close()
    # お試し中
    b,pg,errs=setup(p,"window.__anon=true;")
    pg.click('nav.tabs button[data-tab=admin]');print('trial buttons:',pg.inner_text('#relogin'),'/',pg.inner_text('#logout'))
    pg.locator('#relogin').scroll_into_view_if_needed();pg.screenshot(path=O+'lo1.png')
    pg.click('#relogin');pg.wait_for_timeout(200);pg.screenshot(path=O+'lo2.png');print('warn:',pg.inner_text('#form h3'))
    pg.click('#lvReg');pg.wait_for_timeout(200);print('-> reg sheet:',pg.inner_text('#form h3'))
    pg.click('#cancel');pg.click('#relogin');pg.click('#form button[type=submit]');pg.wait_for_timeout(300);print('trial relogin ->',vis(pg))
    b.close()
    b,pg,errs=setup(p,"window.__anon=true;")
    pg.click('nav.tabs button[data-tab=admin]');pg.click('#logout');pg.click('#form button[type=submit]');pg.wait_for_timeout(300);print('trial logout ->',vis(pg),errs);b.close()
