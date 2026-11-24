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
SEED="""(()=>{const d=window.__db;const t=new Date().toISOString().slice(0,10);const x=new Date();x.setDate(x.getDate()+7);const f=x.toISOString().slice(0,10);
d.bookings.push({id:'bt',salon_id:'s1',customer_id:'c1',stylist_id:'st2',booked_on:t,start_time:'14:00',duration_min:90,menu_names:['カラー'],price:7700,status:'booked'});
d.bookings.push({id:'bf',salon_id:'s1',customer_id:'c1',stylist_id:'st1',booked_on:f,start_time:'11:00',duration_min:60,menu_names:['カット'],price:4800,status:'booked'})})();"""
with sync_playwright() as p:
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=MOCK+SEED,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.goto(INDEX);pg.wait_for_timeout(500)
    st=lambda: {x['id']:x['status'] for x in pg.evaluate('__db.bookings')}
    # 1) カルテから記録 → 今日の予約とつながる
    pg.click('[data-open=c1]');pg.click('#addV');pg.wait_for_timeout(200)
    print('link note:',pg.inner_text('.bklink'));print('prefill menu:',pg.eval_on_selector_all('#mrows select','e=>e.map(x=>x.options[x.selectedIndex].text)'),'price',pg.input_value('#v3'),'stylist',pg.eval_on_selector('#vst','e=>e.options[e.selectedIndex].text'))
    pg.screenshot(path=O+'link.png')
    pg.click('#form button[type=submit]');pg.wait_for_timeout(500);print('after save:',st())
    # 2) 予約のない日 → つながらない
    pg.click('#addV');pg.wait_for_timeout(200);print('no booking today now -> note',pg.locator('.bklink').count())
    # 日付を一週間後に変えて保存 → その日の予約とつながる
    f=pg.evaluate("(()=>{const x=new Date();x.setDate(x.getDate()+7);return x.toISOString().slice(0,10)})()")
    pg.fill('#v1',f);pg.click('#form button[type=submit]');pg.wait_for_timeout(500);print('date changed save:',st())
    pg.click('[data-ev] >> nth=0');pg.click('#delIn');pg.click('#form button[type=submit]');pg.wait_for_timeout(600);print('after delete visit:',st(),'walk-in rows',[x for x in pg.evaluate('__db.bookings') if x.get('walk_in')])
    print(errs);b.close()
