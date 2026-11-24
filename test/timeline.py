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
O=OUT
SEED="""
(()=>{const d=window.__db;const names=[['田中 さくら','たなか さくら'],['鈴木 結衣','すずき ゆい'],['高橋 陽菜','たかはし ひな'],['伊藤 美月','いとう みづき'],['渡辺 葵','わたなべ あおい'],['山本 莉子','やまもと りこ']];
names.forEach(([n,k],i)=>d.customers.push({id:'c'+(i+2),salon_id:'s1',name:n,kana:k,tel:'090-1234-56'+i+i,birthday:'199'+i+'-0'+(i+1)+'-15',hair:'細め',allergy:'',memo:'',face_path:null}));
const t=new Date();const ymd=x=>x.toISOString().slice(0,10);
d.customers.forEach((c,i)=>{for(let j=0;j<3;j++){const dt=new Date(t);dt.setDate(t.getDate()-(i*9+j*35));const id='v'+i+j;d.visits.push({id,salon_id:'s1',customer_id:c.id,stylist_id:'st1',visited_on:ymd(dt),visited_at:'1'+(i%8)+':00',price:4800+i*1000,chem:j==0?'根元 6Lv ナチュラル＋6% 1:1\\n放置 20分':'',memo:j==0?'次回は少し明るめ希望':''});d.visit_menus.push({id:'vm'+i+j,salon_id:'s1',visit_id:id,menu_id:'m0',menu_name:'カット',price:4800,sort:0})}});
[[10,'c1'],[11.5,'c2'],[14,'c3'],[16,'c4']].forEach(([h,c],i)=>d.bookings.push({id:'b'+i,salon_id:'s1',customer_id:c,stylist_id:i%2?'st2':'st1',booked_on:ymd(t),start_time:String(Math.floor(h)).padStart(2,'0')+':'+(h%1?'30':'00'),duration_min:60,menu_names:['カット'],price:4800,status:'booked',memo:''}));
const fam=[['佐々木','ささき'],['山田','やまだ'],['中村','なかむら'],['小林','こばやし'],['加藤','かとう'],['吉田','よしだ'],['松本','まつもと'],['井上','いのうえ'],['木村','きむら'],['林','はやし']],giv=[['あい','あい'],['ゆか','ゆか'],['さき','さき'],['まな','まな'],['りな','りな'],['なな','なな'],['えり','えり'],['みく','みく'],['かな','かな'],['もえ','もえ']];
for(let i=0;i<490;i++){const f=fam[i%10],g=giv[Math.floor(i/10)%10];d.customers.push({id:'x'+i,salon_id:'s1',name:f[0]+' '+g[0]+(i>=100?Math.floor(i/100):''),kana:f[1]+' '+g[1],tel:'080-5555-'+String(1000+i),birthday:null,hair:'',allergy:'',memo:'',face_path:null})}
})();"""
with sync_playwright() as p:
    b=p.chromium.launch(**LAUNCH);pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase-js@*/**',lambda r:r.fulfill(body=MOCK+SEED,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.route('**/functions/v1/**',lambda r:r.fulfill(status=200,body='{"ok":true}',content_type='application/json'))
    pg.goto(INDEX);pg.wait_for_timeout(600)
    pg.evaluate("""()=>{const d=__db;const t=new Date().toISOString().slice(0,10);d.bookings=[];
      d.staff.push({id:'st3',salon_id:'s1',user_id:'u3',login_id:'b',display_name:'スタッフB',role:'staff',is_stylist:true,active:true,sort:0,created_at:'3'});
      d.staff[1].display_name='スタッフA';d.staff[0].display_name='オーナー';
      const B=(id,c,st,time,dur,menu)=>d.bookings.push({id,salon_id:'s1',customer_id:c,stylist_id:st,booked_on:t,start_time:time,duration_min:dur,menu_names:[menu],price:4800,status:'booked'});
      B('k1','c1','st1','09:00',90,'カット');B('k2','c2','st1','10:00',90,'カラー');B('k3','c3','st2','09:30',60,'カット');B('k4','c4','st3','12:00',90,'パーマ')}""")
    pg.click('nav.tabs button[data-tab=admin]');pg.click('#reload');pg.wait_for_timeout(300)
    pg.click('nav.tabs button[data-tab=book]');pg.wait_for_timeout(200);pg.click('[data-bview=tl]');pg.wait_for_timeout(200)
    print('rows',pg.eval_on_selector_all('.tlr .tln','e=>e.map(x=>x.textContent)'),'blocks',pg.locator('.tlb').count())
    print('lanes owner height',pg.eval_on_selector('.tlr','e=>e.style.height'))
    pg.locator('.tlw').scroll_into_view_if_needed();pg.screenshot(path=O+'tl1.png')
    pg.click('[data-tlsel=k2]');pg.wait_for_timeout(200);print('selected card:',pg.inner_text('.book li .who'))
    pg.locator('.book').scroll_into_view_if_needed();pg.screenshot(path=O+'tl2.png')
    pg.reload();pg.wait_for_timeout(600);pg.click('nav.tabs button[data-tab=book]');print('remembered:',pg.locator('.tlw').count())
    pg.set_viewport_size({'width':1000,'height':800});pg.wait_for_timeout(200);pg.screenshot(path=O+'tl3.png')
    print(errs);b.close()
