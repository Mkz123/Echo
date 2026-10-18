from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,base64,hashlib,shutil

repo=Path(__file__).resolve().parents[3]
root=repo/'assets/backgrounds-v3'
data=json.loads((root/'layouts.json').read_text())
assert hashlib.sha256((repo/'echo.html').read_bytes()).hexdigest()==data['sourceHash']
keys={f"{s}-{l['backgroundLayoutNumber']:02d}" for l in data['levels'] for s in l['actualScenes']}
missing=[k for k in keys if not (root/'paintings'/f'{k}.png').exists()]
assert not missing,missing
assets={}
for key in sorted(keys):
 im=Image.open(root/'paintings'/f'{key}.png').convert('RGB')
 im.save(root/'webp'/f'{key}.webp',quality=86,method=6)
 thumb=im.copy();thumb.thumbnail((480,350))
 import io
 b=io.BytesIO();thumb.save(b,format='WEBP',quality=77,method=6)
 assets[key]={'src':'data:image/webp;base64,'+base64.b64encode((root/'webp'/f'{key}.webp').read_bytes()).decode(),'thumb':'data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode(),'width':im.width,'height':im.height}
for scene in data['scenes']:
 levels=[l for l in data['levels'] if scene['id'] in l['actualScenes']]
 cols=min(3,len(levels)); rows=(len(levels)+cols-1)//cols
 sheet=Image.new('RGB',(cols*500,rows*410+90),'#102020');g=ImageDraw.Draw(sheet)
 font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',20)
 titlefont=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',30)
 g.text((20,20),scene['name']+' · 实际关卡整景',font=titlefont,fill='#eceddc')
 for i,l in enumerate(levels):
  key=f"{scene['id']}-{l['backgroundLayoutNumber']:02d}"
  im=Image.open(root/'paintings'/f'{key}.png').convert('RGB');im.thumbnail((476,350))
  x=(i%cols)*500+12;y=(i//cols)*410+90
  sheet.paste(im,(x+(476-im.width)//2,y+(350-im.height)//2))
  g.text((x,y+355),f"{l['number']:02d}  {l['name']}",font=font,fill='#eceddc')
 sheet.save(root/'review'/f"{scene['id']}.jpg",quality=91)
manifest={'version':3,'status':'preview-only','alignment':'source-layout-guided-painting-needs-edge-review','sourceHash':data['sourceHash'],'coreHash':data['coreHash'],'uniquePaintings':len(keys),'entries':[]}
for l in data['levels']:
 for s in l['actualScenes']:
  k=f"{s}-{l['backgroundLayoutNumber']:02d}"
  manifest['entries'].append({'level':l['number'],'name':l['name'],'scene':s,'key':k,'png':f'paintings/{k}.png','webp':f'webp/{k}.webp','guide':f"guides/{l['backgroundLayoutNumber']:02d}.png",'sharedLayout':l['backgroundLayoutNumber']!=l['number']})
(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
payload={'levels':data['levels'],'scenes':data['scenes'],'assets':assets}
template=r'''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ECHO · 整景背景画册</title>
<style>
:root{color-scheme:dark;--ink:#e9eadc;--muted:#9aaea8;--line:#30443f;--accent:#aad5af}*{box-sizing:border-box}body{margin:0;background:#0b1715;color:var(--ink);font:15px/1.65 system-ui,-apple-system,sans-serif}button,select,a{font:inherit}button,select{border:1px solid var(--line);border-radius:8px;background:#14241f;color:var(--ink);padding:8px 12px;cursor:pointer}button:hover,button.active{border-color:var(--accent);background:#283d30}button:disabled{opacity:.35;cursor:default}a{color:#c0d7ad}header{padding:24px 4vw 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:24px;align-items:center}.eyebrow{letter-spacing:.25em;font-size:11px;color:var(--accent)}h1{font:500 clamp(24px,3vw,38px)/1.2 Georgia,serif;margin:7px 0}p{margin:8px 0}.intro{color:var(--muted);max-width:620px;font-size:13px}.counts{text-align:right;font-size:12px;color:var(--muted)}.counts strong{font:34px Georgia;color:var(--ink)}main{padding:20px 4vw 50px;max-width:1800px;margin:auto}.toolbar,.scenes,.overlays{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.toolbar{justify-content:space-between;margin-bottom:14px}.levelbar{display:flex;gap:7px;max-width:100%;align-items:center}select{max-width:min(60vw,320px)}.scenes button{font-size:13px}.stage{position:relative;display:flex;align-items:center;justify-content:center;min-height:240px;background:#08100f;border:1px solid var(--line);border-radius:12px;overflow:hidden}.stage canvas{display:block;max-width:100%;max-height:77vh;width:auto;height:auto;object-fit:contain}.stage.loading{opacity:.6}.caption{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;margin:12px 0 20px}.caption h2{font-size:18px;margin:0}.caption p,.caption a{font-size:12px;color:var(--muted)}.overlays{font-size:12px}.overlays label{display:flex;gap:4px;align-items:center;cursor:pointer}input{accent-color:#a9dbad}.notice{font-size:12px;color:#b3b8a7;border-left:2px solid #697958;padding-left:12px;margin:0 0 25px}.galleryHead{display:flex;justify-content:space-between;align-items:center;margin:32px 0 15px}.galleryHead h2{font-size:17px;margin:0}.galleryHead span{font-size:12px;color:var(--muted)}.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}.card{padding:0;text-align:left;overflow:hidden;border-radius:10px;background:#13231e}.card img{width:100%;height:170px;object-fit:contain;background:#08120e;display:block}.card div{padding:10px 12px}.card strong{font-size:13px;font-weight:500}.card small{display:block;color:var(--muted);font-size:11px}.card.selected{outline:2px solid var(--accent)}footer{font-size:11px;color:var(--muted);margin-top:30px}@media(max-width:650px){header{align-items:start;padding:20px}.counts{min-width:75px}.counts strong{font-size:26px}.intro{font-size:12px}main{padding:16px 14px}.toolbar{align-items:start}.scenes{gap:5px}.scenes button{padding:7px 10px}.gallery{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.card img{height:125px}.card div{padding:8px}.caption{gap:8px}.galleryHead{align-items:start;gap:10px}h1{font-size:27px}}
</style>
<header><div><div class="eyebrow">ECHO / ENVIRONMENT STUDIES 03</div><h1>记忆里的完整场景</h1><p class="intro">连续的走道，连贯的环境。只绘制各关实际出现的场景，网格留在检查层，默认展示完整原画。</p></div><div class="counts"><strong>35</strong> 幅整景<br>15 关 · 36 个组合</div></header>
<main><div class="toolbar"><div class="levelbar"><button id="prev" aria-label="上一关">←</button><select id="level" aria-label="选择关卡"></select><button id="next" aria-label="下一关">→</button></div><div class="scenes" id="scenes"></div></div><div class="stage" id="stage"><canvas id="canvas" aria-label="关卡整景背景"></canvas></div><div class="caption"><div><h2 id="title"></h2><p id="meta"></p></div><div class="overlays"><label><input type="checkbox" id="route">原始路径</label><label><input type="checkbox" id="grid">隐藏网格</label><label><input type="checkbox" id="features">机关位置</label><a id="download" download>保存预览图</a><a id="png" target="_blank">打开 PNG 原画</a></div></div><p class="notice">这是尚未接入游戏的整景原画提案。构图参考原始地图；生成绘画的道路边缘仍需逐处校正，不能视为像素级对齐已通过。门、按钮、箱子、闸机和机器人保持独立图层；勾选检查层可查看原始位置。</p><div class="galleryHead"><h2>全部实际关卡</h2><span>点击任意画面切换 · 首尾空间站共用同一布局</span></div><div class="gallery" id="gallery"></div><footer>内置全部预览图片，直接打开本文件即可，无需联网或启动服务。游戏逻辑与音频未改动。</footer></main>
<script id="data" type="application/json">__DATA__</script><script>
const D=JSON.parse(document.getElementById('data').textContent),$=x=>document.getElementById(x),ctx=$('canvas').getContext('2d'),cache=new Map();let index=0,scene='greenhouse',token=0;
const key=(l,s)=>`${s}-${String(l.backgroundLayoutNumber).padStart(2,'0')}`,sceneInfo=s=>D.scenes.find(x=>x.id===s),checks=['route','grid','features'];
D.levels.forEach((l,i)=>{const o=document.createElement('option');o.value=i;o.textContent=String(l.number).padStart(2,'0')+' · '+l.name;$('level').append(o)});
for(const l of D.levels)for(const s of l.actualScenes){const k=key(l,s),b=document.createElement('button');b.className='card';b.dataset.level=l.id;b.dataset.scene=s;const im=new Image();im.src=D.assets[k].thumb;im.loading='lazy';im.alt=`第 ${l.number} 关 ${sceneInfo(s).name}`;const text=document.createElement('div'),st=document.createElement('strong'),sm=document.createElement('small');st.textContent=`${String(l.number).padStart(2,'0')} · ${l.name}`;sm.textContent=sceneInfo(s).name+(l.number!==l.backgroundLayoutNumber?' · 首尾同布局':'');text.append(st,sm);b.append(im,text);b.onclick=()=>{index=l.id;scene=s;select();$('stage').scrollIntoView({behavior:'smooth',block:'start'})};$('gallery').append(b)}
async function getImage(k){if(cache.has(k))return cache.get(k);const im=new Image();im.src=D.assets[k].src;await im.decode();cache.set(k,im);if(cache.size>6)cache.delete(cache.keys().next().value);return im}
async function select(){const t=++token,l=D.levels[index];if(!l.actualScenes.includes(scene))scene=l.actualScenes[0];$('level').value=index;$('prev').disabled=index===0;$('next').disabled=index===D.levels.length-1;$('scenes').replaceChildren();l.actualScenes.forEach(s=>{const b=document.createElement('button');b.textContent=sceneInfo(s).name;b.className=s===scene?'active':'';b.onclick=()=>{scene=s;select()};$('scenes').append(b)});const k=key(l,scene);$('title').textContent=`${String(l.number).padStart(2,'0')} · ${l.name} / ${sceneInfo(scene).name}`;$('meta').textContent=`${l.actualScenes.length} 个实际场景 · 隐藏布局 ${l.width} × ${l.height}`+(l.number!==l.backgroundLayoutNumber?' · 与第 01 关空间站共用背景':'');$('png').href=`paintings/${k}.png`;$('download').href=D.assets[k].src;$('download').download=k+'.webp';document.querySelectorAll('.card').forEach(b=>b.classList.toggle('selected',+b.dataset.level===index&&b.dataset.scene===scene));$('stage').classList.add('loading');try{const im=await getImage(k);if(t!==token)return;draw(im,l);$('stage').classList.remove('loading')}catch(e){$('meta').textContent='图片读取失败：'+e.message}}
function draw(im,l){const c=$('canvas');c.width=l.width*112;c.height=l.height*112;ctx.drawImage(im,0,0,c.width,c.height);const u=112;
if($('route').checked){ctx.fillStyle='rgba(125,255,194,.20)';ctx.strokeStyle='#96ffd0';ctx.lineWidth=2;for(let y=0;y<l.height;y++)for(let x=0;x<l.width;x++)if(l.terrain[y][x]){ctx.fillRect(x*u,y*u,u,u);const edges=[[0,-1,0,0,1,0],[1,0,1,0,1,1],[0,1,1,1,0,1],[-1,0,0,1,0,0]];for(const [dx,dy,a,b,c,d]of edges)if(!l.terrain[y+dy]?.[x+dx]){ctx.beginPath();ctx.moveTo((x+a)*u,(y+b)*u);ctx.lineTo((x+c)*u,(y+d)*u);ctx.stroke()}}}
if($('grid').checked){ctx.strokeStyle='rgba(255,255,255,.30)';ctx.lineWidth=1;ctx.beginPath();for(let x=0;x<=l.width;x++){ctx.moveTo(x*u,0);ctx.lineTo(x*u,c.height)}for(let y=0;y<=l.height;y++){ctx.moveTo(0,y*u);ctx.lineTo(c.width,y*u)}ctx.stroke()}
if($('features').checked){const colors={start:'#e7f7e5',exit:'#ffd57c',plate:'#adf4bd',door:'#f3947b',inverseDoor:'#ffb3de',box:'#e8bf77',timed:'#c2b5ff',gate:'#8bddff'};ctx.font='bold 24px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';for(const f of l.features){const x=(f.x+.5)*u,y=(f.y+.5)*u;ctx.fillStyle='#11201eee';ctx.strokeStyle=colors[f.type]||'#fff';ctx.lineWidth=3;ctx.beginPath();ctx.arc(x,y,24,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.fillStyle=ctx.strokeStyle;ctx.fillText(f.symbol,x,y)}}}
$('level').onchange=e=>{index=+e.target.value;select()};$('prev').onclick=()=>{if(index>0){index--;select()}};$('next').onclick=()=>{if(index<14){index++;select()}};checks.forEach(id=>$(id).onchange=()=>{const l=D.levels[index],im=cache.get(key(l,scene));if(im)draw(im,l)});document.addEventListener('keydown',e=>{if(e.target.tagName==='SELECT'||e.target.tagName==='INPUT')return;if(e.key==='ArrowLeft')$('prev').click();if(e.key==='ArrowRight')$('next').click()});select();
</script></html>'''
(root/'preview.html').write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')))
print(json.dumps({'unique':len(keys),'entries':len(manifest['entries']),'previewMB':round((root/'preview.html').stat().st_size/1024/1024,1)},ensure_ascii=False))
