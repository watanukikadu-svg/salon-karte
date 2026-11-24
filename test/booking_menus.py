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
    pg.click('nav.tabs button[data-tab=book]');pg.click('#addB');pg.wait_for_timeout(300)
    pg.click('[data-pick=c5]');print('rows',pg.locator('#bmrows select').count(),'x hidden',pg.locator('#bmrows .mx').first.is_hidden())
    pg.click('#addBm');pg.select_option('#bmrows select >> nth=1',label='カラー')
    pg.click('#addBm');pg.select_option('#bmrows select >> nth=2',label='トリートメント');print('sum:',pg.inner_text('#bmsum'))
    pg.screenshot(path=O+'bm.png')
    pg.click('#bmrows .mx >> nth=2');print('after remove:',pg.inner_text('#bmsum'))
    pg.click('#form button[type=submit]');pg.wait_for_timeout(500)
    bk=pg.evaluate('__db.bookings[__db.bookings.length-1]');print('saved',bk['menu_names'],bk['price'],bk['duration_min'])
    li=pg.locator('.book li').filter(has_text='伊藤');print('card:',li.locator('.menu').first.inner_text())
    li.locator('[data-eb]').click();pg.wait_for_timeout(200);print('edit rows',pg.eval_on_selector_all('#bmrows select','e=>e.map(x=>x.value)'));pg.click('#cancel')
    pg.click('[data-open]');pg.click('#addV');pg.wait_for_timeout(200);print('visit menus',pg.eval_on_selector_all('#mrows select','e=>e.map(x=>x.options[x.selectedIndex].text)'),'price',pg.input_value('#v3'))
    print(errs);b.close()
