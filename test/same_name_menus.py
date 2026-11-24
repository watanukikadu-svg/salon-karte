# このファイルは test/ にある。python3 test/<名前>.py で動かす（リポジトリの一番上で）
# 同じ名前のメニュー（カット4500円・カット4000円）を登録して、予約と施術記録で取りちがえないか
import os, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
INDEX = 'file://' + os.path.join(ROOT, 'index.html')
OUT = os.path.join(HERE, 'out') + '/'; os.makedirs(OUT, exist_ok=True)
MOCK_PATH = os.path.join(HERE, 'mock-supabase.js')
_exe = glob.glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome'); LAUNCH = dict(executable_path=_exe[0]) if _exe else {}
from playwright.sync_api import sync_playwright
MOCK = open(MOCK_PATH).read()
with sync_playwright() as p:
    b = p.chromium.launch(**LAUNCH); pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase-js@*/**', lambda r: r.fulfill(body=MOCK, content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.goto(INDEX); pg.wait_for_timeout(500)
    def add_menu(name, price, dur):
        pg.click('#addM'); pg.fill('#m1', name); pg.fill('#m2', str(price)); pg.fill('#m3', str(dur)); pg.click('#form button[type=submit]'); pg.wait_for_timeout(300)
    pg.click('nav.tabs button[data-tab=admin]')
    add_menu('カット', 4000, 45)
    print('same name ok:', [(m['name'], m['price']) for m in pg.evaluate('__db.menus') if m['name'] == 'カット'])
    add_menu('カット', 4000, 45); print('exact duplicate blocked:', pg.inner_text('#toastMsg')); pg.click('#cancel')
    # 予約：カット（¥4,000）を選ぶ
    pg.click('nav.tabs button[data-tab=book]'); pg.click('#addB'); pg.fill('#b1q', 'さとう'); pg.click('#b1res .pk-row >> nth=0')
    print('options:', pg.eval_on_selector('#bmrows select', 'e=>[...e.options].map(o=>o.text)'))
    pg.select_option('#bmrows select', label='カット（¥4,000）'); pg.wait_for_timeout(100); print('price shown:', pg.inner_text('#bmrows .mp'))
    pg.click('#form button[type=submit]'); pg.wait_for_timeout(400)
    bk = pg.evaluate('__db.bookings[__db.bookings.length-1]'); print('saved:', bk['menu_names'], bk['price'], bk['duration_min'], 'ids set', bool(bk['menu_ids'][0]))
    pg.click('[data-eb] >> nth=0'); print('edit preselect:', pg.eval_on_selector('#bmrows select', 'e=>e.options[e.selectedIndex].text')); pg.click('#cancel')
    # カルテから施術を記録 → 予約のカット（¥4,000）が入っている
    pg.click('[data-open] >> nth=0'); pg.click('#addV'); pg.wait_for_timeout(200)
    print('visit preselect:', pg.eval_on_selector_all('#mrows select', 'e=>e.map(x=>x.options[x.selectedIndex].text)'), 'price', pg.input_value('#v3'))
    pg.click('#form button[type=submit]'); pg.wait_for_timeout(500)
    v = pg.evaluate('__db.visit_menus[__db.visit_menus.length-1]'); print('visit saved:', v['menu_name'], v['list_price'])
    # 来店履歴を編集しても ¥4,000 のまま
    pg.click('[data-ev] >> nth=0'); print('visit edit preselect:', pg.eval_on_selector('#mrows select', 'e=>e.options[e.selectedIndex].text'), errs)
    b.close()
