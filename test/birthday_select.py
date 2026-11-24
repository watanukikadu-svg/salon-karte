# このファイルは test/ にある。python3 test/<名前>.py で動かす（リポジトリの一番上で）
# 新しいお客様の誕生日を「年・月・日」の3つの選択で入れられるか（カレンダーの小窓を使わない）
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
    last = lambda: pg.evaluate('__db.customers[__db.customers.length-1]')
    pg.click('#addC'); pg.wait_for_timeout(200)
    print('date calendar input remains:', pg.locator('#form input[type=date]').count())
    pg.locator('.bday').scroll_into_view_if_needed(); pg.screenshot(path=OUT + 'bday.png')
    pg.fill('#f1', '誕生日 未登録'); pg.click('#form button[type=submit]'); pg.wait_for_timeout(300); print('empty ->', last()['name'], last()['birthday'])
    pg.click('#back'); pg.click('#addC'); pg.fill('#f1', '途中まで'); pg.select_option('select[name=by]', '1992'); pg.click('#form button[type=submit]'); pg.wait_for_timeout(300); print('partial ->', pg.inner_text('#toastMsg'))
    pg.select_option('select[name=bm]', '2'); pg.select_option('select[name=bd]', '30'); pg.click('#form button[type=submit]'); pg.wait_for_timeout(300); print('2/30 ->', pg.inner_text('#toastMsg'))
    pg.select_option('select[name=bd]', '29'); pg.click('#form button[type=submit]'); pg.wait_for_timeout(300); print('1992/2/29 (うるう年) ->', last()['name'], last()['birthday'])
    pg.click('#editC'); pg.wait_for_timeout(200); print('edit keeps:', [pg.eval_on_selector(f'select[name={n}]', 'e=>e.value') for n in ('by', 'bm', 'bd')])
    for n in ('by', 'bm', 'bd'): pg.select_option(f'select[name={n}]', '')
    pg.click('#form button[type=submit]'); pg.wait_for_timeout(300); print('cleared ->', last()['birthday'], errs)
    b.close()
