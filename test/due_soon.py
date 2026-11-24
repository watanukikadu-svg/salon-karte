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
SEED="""(()=>{const d=window.__db;d.customers=[];d.visits=[];d.bookings=[];const t=new Date();const ago=n=>{const x=new Date(t);x.setDate(x.getDate()-n);return x.toISOString().slice(0,10)};const fut=n=>{const x=new Date(t);x.setDate(x.getDate()+n);return x.toISOString().slice(0,10)};
const C=(id,name,kana,vs)=>{d.customers.push({id,salon_id:'s1',name,kana,tel:'',birthday:null,hair:'',allergy:'',memo:'',face_path:null});vs.forEach((n,i)=>d.visits.push({id:id+'v'+i,salon_id:'s1',customer_id:id,visited_on:ago(n),visited_at:'10:00',price:4800}))};
C('a','A 30日ごと・あと5日','えー',[85,55,25]);C('b','B 30日ごと・5日すぎ','びー',[95,65,35]);C('c','C 60日ごと・まだ先','しー',[130,70,10]);
C('d','D 1回だけ・40日前','でぃー',[40]);C('e','E 30日ごと・ずっと来ない','いー',[160,130,100]);C('f','F 予約あり','えふ',[90,60,30]);C('g','G 今日が目安','じー',[60,30]);
d.bookings.push({id:'bf',salon_id:'s1',customer_id:'f',stylist_id:'st1',booked_on:fut(3),start_time:'10:00',duration_min:60,menu_names:['カット'],price:4800,status:'booked'})})();"""
with sync_playwright() as p:
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=MOCK+SEED,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.goto(INDEX);pg.wait_for_timeout(500)
    pg.click('nav.tabs button[data-tab=book]');pg.click('#addB');pg.wait_for_timeout(300)
    print(pg.inner_text('#b1res .hint >> nth=0'))
    for r in pg.query_selector_all('#b1res .pk-row'): print(' ',r.query_selector('.nm').inner_text(),'|',r.query_selector('.last').inner_text().replace('\n',' / '))
    pg.screenshot(path=O+'due.png');print(errs);b.close()
