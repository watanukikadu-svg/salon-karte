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
    bks=lambda: [(x['booked_on'],x['start_time'],x['menu_names'],x['status'],x.get('walk_in'),bool(x.get('visit_id'))) for x in pg.evaluate('__db.bookings')]
    # 予約なしで記録
    pg.click('[data-open=c1]');pg.click('#addV');pg.wait_for_timeout(200);print('note shown?',pg.locator('.bklink').count())
    pg.fill('#v1t','15:30');pg.click('#addMr');pg.select_option('#mrows select >> nth=1','1')
    pg.click('#form button[type=submit]');pg.wait_for_timeout(500);print('after record:',bks())
    pg.click('nav.tabs button[data-tab=book]');pg.wait_for_timeout(200);print('card:',pg.inner_text('.book li >> nth=0').replace('\n',' | '))
    pg.screenshot(path=O+'walk.png')
    # 記録を直すと予約も直る
    pg.click('nav.tabs button[data-tab=cust]');pg.click('[data-open=c1]');pg.click('[data-ev] >> nth=0');pg.fill('#v1t','16:00');pg.click('#form button[type=submit]');pg.wait_for_timeout(500);print('after edit:',bks())
    # 記録を消すと予約も消える
    pg.click('[data-ev] >> nth=0');pg.click('#delIn');pg.click('#form button[type=submit]');pg.wait_for_timeout(600);print('after delete:',bks(),errs)
    b.close()
