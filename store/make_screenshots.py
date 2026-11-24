# App Store 用の画面写真を作る（6.9インチ iPhone：1320×2868）
# 使い方（リポジトリの一番上で）：python3 store/make_screenshots.py
# 見本のデータ（架空のお客様・予約・売上）を入れたアプリの本物の画面に、上に短い説明をつける。
import os, glob, ssl, urllib.request, base64, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'screenshots'); os.makedirs(OUT, exist_ok=True)
MOCK = open(os.path.join(ROOT, 'test', 'mock-supabase.js')).read()
_exe = glob.glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome'); LAUNCH = dict(executable_path=_exe[0]) if _exe else {}
from playwright.sync_api import sync_playwright

# 字体（Zen Kaku Gothic New・Outfit）はネットから取ってきて渡す
_ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt') if os.path.exists('/root/.ccr/ca-bundle.crt') else None
_cache = {}
def fetch(url, ua=True):
    if url not in _cache:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'})
        with urllib.request.urlopen(req, context=_ctx, timeout=30) as r: _cache[url] = (r.read(), r.headers.get('Content-Type', ''))
    return _cache[url]
def font_route(route):
    try: body, ct = fetch(route.request.url); route.fulfill(body=body, content_type=ct)
    except Exception: route.fulfill(body='', content_type='text/css')

# 見本のデータ（名前はすべて架空）
SEED = r"""(()=>{const d=window.__db;const t=new Date();const ymd=x=>x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0');const ago=n=>{const x=new Date(t);x.setDate(x.getDate()-n);return ymd(x)};const fut=n=>{const x=new Date(t);x.setDate(x.getDate()+n);return ymd(x)};
d.salons[0].name='Hair Salon Lumière';
d.staff=[{id:'st1',salon_id:'s1',user_id:'u1',login_id:'owner',display_name:'山口',role:'owner',is_stylist:true,can_view_sales:true,can_edit_master:true,can_delete_customers:true,can_manage_staff:true,active:true,sort:0,created_at:'1'},
 {id:'st2',salon_id:'s1',user_id:'u2',login_id:'ito',display_name:'伊藤',role:'staff',is_stylist:true,can_view_sales:false,can_edit_master:false,can_delete_customers:false,can_manage_staff:false,active:true,sort:1,created_at:'2'},
 {id:'st3',salon_id:'s1',user_id:'u3',login_id:'mori',display_name:'森',role:'staff',is_stylist:true,can_view_sales:false,can_edit_master:false,can_delete_customers:false,can_manage_staff:false,active:true,sort:2,created_at:'3'}];
d.menus=[['カット',4800,60],['カット＋カラー',11000,120],['カラー',7700,90],['パーマ',12100,120],['縮毛矯正',18700,180],['トリートメント',4400,30]].map(([name,price,duration_min],i)=>({id:'m'+i,salon_id:'s1',name,price,duration_min,sort:i,active:true,created_at:''+i}));
d.products=[{id:'p1',salon_id:'s1',name:'ヘアオイル',price:3300,stock:12,sort:0,active:true,created_at:'1'},{id:'p2',salon_id:'s1',name:'シャンプー',price:2860,stock:2,sort:1,active:true,created_at:'2'}];
const C=[['c1','佐藤 美咲','さとう みさき','090-1234-5678','1992-'+ymd(new Date(t.getTime()+6*864e5)).slice(5),'細め・クセあり','ジアミン','前髪は眉上が好み。次回は少し明るめ希望'],
 ['c2','高橋 陽菜','たかはし ひな','080-2345-6789','1998-04-12','普通・多い','','耳かけしやすい長さ'],['c3','田中 さくら','たなか さくら','070-3456-7890','1989-09-30','太め','',''],
 ['c4','伊藤 美月','いとう みづき','090-4567-8901','2001-01-18','細め','',''],['c5','渡辺 葵','わたなべ あおい','080-5678-9012','1995-06-07','普通','',''],
 ['c6','山本 莉子','やまもと りこ','090-6789-0123','1987-11-23','クセ強め','',''],['c7','中村 結衣','なかむら ゆい','070-7890-1234','1999-03-03','普通','',''],
 ['c8','小林 花','こばやし はな','080-8901-2345','1993-08-15','細め','',''],['c9','加藤 楓','かとう かえで','090-9012-3456','2000-12-24','多い','',''],['c10','吉田 七海','よしだ ななみ','070-0123-4567','1990-05-05','普通','','']];
d.customers=C.map(([id,name,kana,tel,birthday,hair,allergy,memo])=>({id,salon_id:'s1',name,kana,tel,birthday,hair,allergy,memo,face_path:null}));
const V=(id,c,daysAgo,time,st,menus,price,chem,memo,items)=>{d.visits.push({id,salon_id:'s1',customer_id:c,stylist_id:st,nominated:st!=='st1',visited_on:ago(daysAgo),visited_at:time,price,chem:chem||'',memo:memo||''});menus.forEach((m,i)=>{const mm=d.menus.find(x=>x.name===m);d.visit_menus.push({id:id+'m'+i,salon_id:'s1',visit_id:id,menu_id:mm.id,menu_name:m,list_price:mm.price,sort:i})});(items||[]).forEach((x,i)=>d.visit_items.push({id:id+'i'+i,salon_id:'s1',visit_id:id,product_id:x[0],name:d.products.find(p=>p.id===x[0]).name,price:d.products.find(p=>p.id===x[0]).price,qty:x[1]}))};
V('v1','c1',2,'14:00','st1',['カット＋カラー'],11000,'根元 6Lv ナチュラル＋6% 1:1\n毛先 8Lv アッシュ＋3% 1:1.5\n放置 20分','次回は少し明るめ希望',[['p1',1]]);
V('v2','c1',37,'11:00','st1',['カット','トリートメント'],9200,'','');V('v3','c1',73,'15:30','st1',['カット＋カラー'],11000,'根元 6Lv ナチュラル＋6% 1:1','');
let n=4;const cs=['c2','c3','c4','c5','c6','c7','c8','c9','c10'];const ms=[['カット'],['カラー'],['カット＋カラー'],['パーマ'],['縮毛矯正'],['カット','トリートメント']];
for(let k=0;k<26;k++){const c=cs[k%cs.length],m=ms[k%ms.length];V('v'+(n++),c,(k*3)%40+1,(10+k%8)+':00',['st1','st2','st3'][k%3],m,m.reduce((s,x)=>s+d.menus.find(y=>y.name===x).price,0),'','',k%4===0?[['p1',1]]:[])}
for(let k=0;k<40;k++){const c=cs[k%cs.length],m=ms[(k+2)%ms.length];V('v'+(n++),c,40+k*4,(10+k%8)+':00',['st1','st2','st3'][k%3],m,m.reduce((s,x)=>s+d.menus.find(y=>y.name===x).price,0),'','',[])}
const B=(id,c,day,time,st,menus,items)=>{const mm=menus.map(x=>d.menus.find(y=>y.name===x));d.bookings.push({id,salon_id:'s1',customer_id:c,stylist_id:st,nominated:false,booked_on:day,start_time:time,duration_min:mm.reduce((s,x)=>s+x.duration_min,0),menu_names:menus,menu_ids:mm.map(x=>x.id),price:mm.reduce((s,x)=>s+x.price,0),status:'booked',items:items||[]})};
const T0=ymd(t);B('b1','c2',T0,'10:00','st1',['カット＋カラー']);B('b2','c3',T0,'10:30','st2',['パーマ']);B('b3','c4',T0,'13:00','st1',['カット'],[{product_id:'p1',name:'ヘアオイル',price:3300,qty:1}]);B('b4','c5',T0,'14:00','st3',['縮毛矯正']);B('b5','c6',T0,'16:00','st2',['カラー']);
B('b6','c1',fut(33),'14:00','st1',['カット＋カラー']);B('b7','c7',fut(1),'11:00','st1',['カット']);B('b8','c8',fut(3),'15:00','st2',['カラー']);
})();"""

CAPTIONS = [
  ('1-customers', 'お客様カルテを、スマホひとつで', 'ふりがな・電話で、すぐに見つかる'),
  ('2-carte', 'お客様のことが、ひと目でわかる', 'アレルギー・誕生日・来店履歴・使った薬剤'),
  ('3-booking', '今日の予約を、すっきり確認', 'カレンダーとカードで、予約がひと目で'),
  ('4-timeline', 'スタッフの予定もタイムラインで', '重なる予約も、ひと目でわかる'),
  ('5-record', '施術の記録は、その場でかんたん', 'メニュー・店販・薬剤・写真をまとめて記録'),
  ('6-sales', '売上も、自動で集計', 'スタッフ別・メニュー別・月ごとの推移'),
]

FRAME = """<!doctype html><html><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@500;700&display=swap" rel="stylesheet">
<style>html,body{margin:0;width:440px;height:956px;overflow:hidden}body{background:linear-gradient(170deg,#0b2347 0%,#011636 60%);font-family:'Zen Kaku Gothic New',sans-serif;color:#fff;position:relative}
.cap{position:absolute;top:0;left:0;right:0;height:150px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:0 18px;text-align:center}
.t{font-size:25px;font-weight:700;letter-spacing:.02em;line-height:1.3}.s{font-size:15px;color:#e9c46a;font-weight:500;line-height:1.4}
.ph{position:absolute;left:38px;top:156px;width:364px;border-radius:38px;overflow:hidden;box-shadow:0 18px 50px rgb(0 0 0/.45);border:6px solid #1d2b3f}.ph img{display:block;width:100%}</style></head>
<body><div class="cap"><div class="t">__T__</div><div class="s">__S__</div></div><div class="ph"><img src="data:image/png;base64,__IMG__"></div></body></html>"""

with sync_playwright() as p:
    b = p.chromium.launch(args=['--lang=ja-JP'], env={**os.environ, 'LANG': 'ja_JP.UTF-8', 'LANGUAGE': 'ja'}, **LAUNCH)
    # 1) アプリの画面をとる（390×844 を3倍）
    pg = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=3, locale='ja-JP', timezone_id='Asia/Tokyo')
    pg.route('**/supabase-js@*/**', lambda r: r.fulfill(body=MOCK + SEED, content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**', font_route); pg.route('**/fonts.gstatic.com/**', font_route)
    pg.goto('file://' + os.path.join(ROOT, 'index.html')); pg.wait_for_timeout(1500)
    shots = {}
    def snap(key): pg.wait_for_timeout(400); shots[key] = pg.screenshot()
    snap('1-customers')
    pg.click('[data-open=c1]'); pg.wait_for_timeout(300); snap('2-carte')
    pg.click('#back'); pg.click('nav.tabs button[data-tab=book]'); pg.click('[data-bview=list]'); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('.bhead').scrollIntoView();scrollBy(0,-330)"); snap('3-booking')
    pg.click('[data-bview=tl]'); pg.wait_for_timeout(300); pg.evaluate("document.querySelector('.tlw').scrollLeft=0"); pg.click('[data-tlsel=b1]'); pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('.tlw').scrollLeft=0;document.querySelector('.bhead').scrollIntoView();scrollBy(0,-20)"); snap('4-timeline')
    pg.click('[data-bview=list]'); pg.evaluate("scrollTo(0,0)")
    pg.click('nav.tabs button[data-tab=cust]'); pg.click('[data-open=c4]'); pg.click('#addV'); pg.wait_for_timeout(400); snap('5-record'); pg.click('#cancel')
    pg.click('nav.tabs button[data-tab=sales]'); pg.wait_for_timeout(300); snap('6-sales')
    pg.close()
    # 2) 説明をつけて 1320×2868 にする
    fp = b.new_page(viewport={'width': 440, 'height': 956}, device_scale_factor=3)
    fp.route('**/fonts.googleapis.com/**', font_route); fp.route('**/fonts.gstatic.com/**', font_route)
    for key, t, s in CAPTIONS:
        html = FRAME.replace('__T__', t).replace('__S__', s).replace('__IMG__', base64.b64encode(shots[key]).decode())
        fp.set_content(html); fp.wait_for_timeout(600)
        fp.screenshot(path=os.path.join(OUT, key + '.png'))
        print('作成:', key)
    b.close()
