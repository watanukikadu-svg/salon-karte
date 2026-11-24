# このファイルは test/ にある。python3 test/<名前>.py で動かす（リポジトリの一番上で）
import os, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
INDEX = 'file://' + os.path.join(ROOT, 'index.html')
OUT = os.path.join(HERE, 'out') + '/'; os.makedirs(OUT, exist_ok=True)
MOCK_PATH = os.path.join(HERE, 'mock-supabase.js')
_exe = glob.glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome'); LAUNCH = dict(executable_path=_exe[0]) if _exe else {}
from playwright.sync_api import sync_playwright
MOCK=open(MOCK_PATH).read()
SEED="""(()=>{const d=window.__db;const f=n=>{const x=new Date();x.setDate(x.getDate()+n);return x.toISOString().slice(0,10)};
d.bookings.push({id:'u1',salon_id:'s1',customer_id:'c1',stylist_id:'st2',nominated:true,booked_on:f(7),start_time:'14:00',duration_min:150,menu_names:['カット','カラー'],price:12500,status:'booked',items:[{product_id:'p1',name:'シャンプー',price:3300,qty:1}]});
d.bookings.push({id:'u2',salon_id:'s1',customer_id:'c1',stylist_id:'st1',booked_on:f(2),start_time:'10:00',duration_min:60,menu_names:['カット'],price:4800,status:'booked',items:[]});
d.bookings.push({id:'u3',salon_id:'s1',customer_id:'c1',stylist_id:'st1',booked_on:f(-3),start_time:'10:00',duration_min:60,menu_names:['カット'],price:4800,status:'booked',items:[]});
d.bookings.push({id:'u4',salon_id:'s1',customer_id:'c1',stylist_id:'st1',booked_on:f(0),start_time:'09:00',duration_min:60,menu_names:['カット'],price:4800,status:'done',items:[]})})();"""
with sync_playwright() as p:
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=MOCK+SEED,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.goto(INDEX);pg.wait_for_timeout(500)
    pg.click('[data-open=c1]');pg.wait_for_timeout(200)
    print([x.inner_text().replace('\n',' | ') for x in pg.query_selector_all('.visit.upb')])
    pg.locator('.upb').first.scroll_into_view_if_needed();pg.screenshot(path=OUT+'up.png')
    pg.click('.upb [data-delb] >> nth=0');pg.wait_for_timeout(300);print('after cancel count',pg.locator('.upb').count())
    pg.click('#undo');pg.wait_for_timeout(300);print('after undo',pg.locator('.upb').count())
    pg.click('.upb [data-eb] >> nth=0');print('edit opens:',pg.inner_text('#form h3'),errs)
    b.close()
