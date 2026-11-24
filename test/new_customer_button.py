# このファイルは test/ にある。python3 test/<名前>.py で動かす（リポジトリの一番上で）
# 顧客一覧の「＋ 新しいお客様」が、お客様が100人いても右下にいつも出て押せるか（スマホ・PC）
import os, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
INDEX = 'file://' + os.path.join(ROOT, 'index.html')
OUT = os.path.join(HERE, 'out') + '/'; os.makedirs(OUT, exist_ok=True)
MOCK_PATH = os.path.join(HERE, 'mock-supabase.js')
_exe = glob.glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome'); LAUNCH = dict(executable_path=_exe[0]) if _exe else {}
from playwright.sync_api import sync_playwright
MOCK = open(MOCK_PATH).read()
SEED = "(()=>{const d=window.__db;for(let i=0;i<100;i++)d.customers.push({id:'x'+i,salon_id:'s1',name:'お客様'+i,kana:'おきゃくさま'+i,tel:'',birthday:null,hair:'',allergy:'',memo:'',face_path:null})})();"
with sync_playwright() as p:
    b = p.chromium.launch(**LAUNCH)
    for name, vp in [('phone', {'width': 390, 'height': 844}), ('pc', {'width': 1280, 'height': 800})]:
        pg = b.new_page(viewport=vp); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route('**/supabase-js@*/**', lambda r: r.fulfill(body=MOCK + SEED, content_type='application/javascript'))
        pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
        pg.goto(INDEX); pg.wait_for_timeout(500)
        box = pg.locator('#addC').bounding_box(); nav = pg.locator('nav.tabs').bounding_box(); main = pg.locator('main').bounding_box()
        inview = box['y'] + box['height'] <= nav['y'] and box['x'] + box['width'] <= vp['width']
        print(name, 'customers', pg.locator('.list li button').count(), '| button in view without scroll:', inview, '| above tabs by', round(nav['y'] - (box['y'] + box['height'])), 'px', '| right edge inside main:', box['x'] + box['width'] <= main['x'] + main['width'] + 1)
        pg.screenshot(path=OUT + f'fab_{name}.png')
        pg.mouse.wheel(0, 20000); pg.wait_for_timeout(300)
        last = pg.locator('.list li button').last.bounding_box(); b2 = pg.locator('#addC').bounding_box()
        print('  after scroll to bottom: button still same place', abs(b2['y'] - box['y']) < 1, '| last customer not hidden by button', last['y'] + last['height'] <= b2['y'] or last['x'] + last['width'] <= b2['x'])
        pg.click('#addC'); print('  opens:', pg.inner_text('#form h3')); pg.click('#cancel')
        pg.click('.list li button >> nth=0'); pg.wait_for_timeout(200); print('  on carte: button shown', pg.locator('#addC').count())
        pg.click('nav.tabs button[data-tab=book]'); print('  on bookings tab: button shown', pg.locator('#addC').count(), errs)
        pg.close()
    b.close()
