const FONT='"PingFang SC","Microsoft YaHei",sans-serif';
const TILE=96;
const SLOT_NAMES=['floor','wall','plate-idle','plate-active','timed-idle','timed-active','box','door-closed','door-open','inverse-closed','gate-ready','gate-used','robot-front','robot-left','robot-right','robot-back'];
const CHANNELS=['#3fd0ff','#ff5fa2','#b6ff5c','#ffb347'];
const bitmaps={},spriteBounds={},atlasCuts={};
const qs=s=>document.querySelector(s);
let selectedLevel=13,selectedScene='greenhouse',view='composite',grid=true,labels=true,triggered=false,facing='front';
function canvas(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;return c;}
async function loadArt(){
 for(const id of Object.keys(SPECS)){
  const im=new Image();im.src=ATLAS_DATA[id];await im.decode();bitmaps[id]=im;
  const c=canvas(im.naturalWidth,im.naturalHeight),g=c.getContext('2d',{willReadFrequently:true});g.drawImage(im,0,0);
  const W=c.width,H=c.height,all=g.getImageData(0,0,W,H).data,rows=Array(H).fill(0),columns=Array(W).fill(0);
  for(let y=0;y<H;y++)for(let x=0;x<W;x++)if(all[(y*W+x)*4+3]>40){rows[y]++;columns[x]++;}
  function cuts(profile){
   const n=profile.length,result=[0];
   for(let k=1;k<4;k++){
    const a=Math.floor(n*k/4-n*.09),b=Math.ceil(n*k/4+n*.09),min=Math.min(...profile.slice(a,b));
    const candidates=[];for(let i=a;i<b;i++)if(profile[i]===min)candidates.push(i);
    if(min!==0)throw Error(id+' 图集缺少透明切分间隙');
    // Find the contiguous transparent run closest to the nominal division and cut through its middle.
    const groups=[];let group=[];for(const i of candidates){if(group.length&&i>group[group.length-1]+1){groups.push(group);group=[]}group.push(i)}if(group.length)groups.push(group);
    groups.sort((u,v)=>Math.abs((u[0]+u[u.length-1])/2-n*k/4)-Math.abs((v[0]+v[v.length-1])/2-n*k/4));
    const best=groups[0];result.push(Math.round((best[0]+best[best.length-1])/2));
   }return result.concat(n);
  }
  const xs=cuts(columns),ys=cuts(rows);atlasCuts[id]={columns:xs,rows:ys};
  spriteBounds[id]=Array.from({length:16},(_,i)=>{
   const col=i%4,row=Math.floor(i/4),sx=xs[col],sy=ys[row],w=xs[col+1]-sx,h=ys[row+1]-sy,d=g.getImageData(sx,sy,w,h).data;
   let minX=w,minY=h,maxX=-1,maxY=-1,eyeN=0,eyeX=0;
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){const k=(y*w+x)*4;if(d[k+3]>40){minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);if(i>=12&&d[k+1]>100&&d[k+2]>105&&d[k]<d[k+1]*.66&&d[k]<d[k+2]*.66){eyeN++;eyeX+=x;}}}
   if(maxX<0)throw Error(id+' 空素材格 '+i);
   return {x:sx+minX,y:sy+minY,w:maxX-minX+1,h:maxY-minY+1,eyePixels:eyeN,eyeX:eyeN?eyeX/eyeN/w:null};
  });
 }
}

function actualSlot(id,slot){
 // Direction mapping is verified from the rendered eyes / silhouette, not assumed from column order.
 if(slot===13||slot===14){const a=spriteBounds[id][13].eyeX,b=spriteBounds[id][14].eyeX;if(a!==null&&b!==null){const left=a<b?13:14;return slot===13?left:(left===13?14:13);}}
 return slot;
}
function drawSprite(g,id,slot,x,y,size,scale=.86){
 slot=actualSlot(id,slot);const im=bitmaps[id],b=spriteBounds[id][slot],s=Math.min(size*scale/b.w,size*scale/b.h),w=b.w*s,h=b.h*s;
 g.save();g.beginPath();g.rect(x,y,size,size);g.clip();
 g.drawImage(im,b.x,b.y,b.w,b.h,x+(size-w)/2,y+(size-h)/2,w,h);g.restore();
}
function tile(g,id,isFloor,x,y,size){
 const sp=SPECS[id],im=bitmaps[id],sw=im.naturalWidth/4,sh=im.naturalHeight/4;
 g.save();g.beginPath();g.rect(x,y,size,size);g.clip();
 g.fillStyle=isFloor?sp.floor:sp.wall;g.fillRect(x,y,size,size);
 if(isFloor){
  // Sample only a plain patch of material, discarding the generated tile's internal decorative subdivisions.
  g.globalAlpha=.75;g.drawImage(im,sw*.26,sh*.26,sw*.16,sh*.16,x,y,size,size);g.globalAlpha=1;
  g.fillStyle='rgba(255,247,216,.07)';g.fillRect(x+3,y+3,size-6,size-6);
  g.strokeStyle='rgba(23,31,29,.48)';g.lineWidth=1.5;g.strokeRect(x+1,y+1,size-2,size-2);
 }else{drawSprite(g,id,1,x,y,size,1.05);g.fillStyle='rgba(9,20,19,.1)';g.fillRect(x,y,size,size);}
 g.restore();
}
function mechanism(g,id,feature,L,size,options){
 const {x,y,type,channel}=feature,px=x*size,py=y*size;
 if(type==='start'||type==='exit')return;
 let slot;
 if(type==='plate')slot=options.triggered?3:2;
 if(type==='timed')slot=options.triggered?5:4;
 if(type==='box')slot=6;
 if(type==='gate')slot=options.triggered?11:10;
 if(type==='door'||type==='inverseDoor'){
  const door=L.initialDoors.find(d=>d.x===x&&d.y===y),open=options.triggered?type==='door':door.open;
  slot=open?8:type==='inverseDoor'?9:7;
 }
 drawSprite(g,id,slot,px,py,size,type==='door'||type==='inverseDoor'?.95:.8);
 if(channel!==null){
  const col=CHANNELS[channel];g.strokeStyle=col;g.lineWidth=Math.max(1.5,size*.025);g.strokeRect(px+size*.07,py+size*.07,size*.86,size*.86);
  if(options.labels){g.fillStyle='#102223';g.fillRect(px+4,py+4,size*.23,size*.24);g.fillStyle=col;g.font=`bold ${size*.17}px monospace`;g.textAlign='center';g.textBaseline='middle';g.fillText('ABCD'[channel],px+4+size*.115,py+4+size*.12);}
 }
 if(type==='inverseDoor'){
  g.strokeStyle='#e7c981';g.lineWidth=2;for(let k=0;k<3;k++){g.beginPath();g.moveTo(px+size*(.68+k*.07),py+size*.05);g.lineTo(px+size*(.57+k*.07),py+size*.18);g.stroke();}
 }
}
function renderMap(L,id,size=TILE,options={}){
 options={layer:'composite',grid:true,labels:true,triggered:false,robot:true,facing:'front',...options};
 const c=canvas(L.width*size,L.height*size),g=c.getContext('2d');g.imageSmoothingEnabled=true;
 const conditional=new Set(L.features.filter(f=>['door','inverseDoor','box','gate','exit'].includes(f.type)).map(f=>f.x+','+f.y));
 const drawnMask=[];
 for(let y=0;y<L.height;y++){const row=[];for(let x=0;x<L.width;x++){
  const floor=L.terrain[y][x];row.push(floor);
  if(options.layer==='mask'){
   g.fillStyle=floor?(conditional.has(x+','+y)?'#e5be6e':'#88c6a6'):'#25332f';g.fillRect(x*size,y*size,size,size);
  }else tile(g,id,floor,x*size,y*size,size);
  if(options.grid){g.strokeStyle=floor?'rgba(245,241,209,.22)':'rgba(235,242,221,.12)';g.lineWidth=1;g.strokeRect(x*size+.5,y*size+.5,size-1,size-1);}
 }drawnMask.push(row);}
 c.layoutMask=drawnMask;
 if(options.layer==='composite'){
  L.features.forEach(f=>mechanism(g,id,f,L,size,options));
  const [ex,ey]=L.exit;g.strokeStyle=id==='station'?'#bceccf':'#677e73';g.lineWidth=3;g.setLineDash(id==='station'?[]:[5,4]);g.beginPath();g.arc((ex+.5)*size,(ey+.5)*size,size*.29,0,Math.PI*2);g.stroke();g.setLineDash([]);
  if(options.labels){g.font=`700 ${size*.13}px sans-serif`;g.textAlign='center';g.textBaseline='middle';g.fillStyle=id==='station'?'#e9ffe1':'#a0b3a9';g.fillText(id==='station'?'出口':'未开放',(ex+.5)*size,(ey+.5)*size);}
  if(options.robot){const [x,y]=L.start;drawSprite(g,id,{front:12,left:13,right:14,back:15}[options.facing],x*size,y*size,size,.91);}
 }
 return c;
}
function coordinateFrame(c,L){
 const pad=30,out=canvas(c.width+pad,c.height+pad),g=out.getContext('2d'),size=c.width/L.width;
 g.fillStyle='#0f211e';g.fillRect(0,0,out.width,out.height);g.drawImage(c,pad,pad);
 g.fillStyle='#9caf9f';g.font='11px monospace';g.textAlign='center';g.textBaseline='middle';
 for(let x=0;x<L.width;x++)g.fillText(x,pad+(x+.5)*size,14);
 for(let y=0;y<L.height;y++)g.fillText(y,14,pad+(y+.5)*size);
 return out;
}
function show(){
 const L=DATA.levels[selectedLevel],id=selectedScene;
 const c=coordinateFrame(renderMap(L,id,TILE,{layer:view,grid,labels,triggered,facing}),L);
 const target=qs('#map');target.width=c.width;target.height=c.height;target.getContext('2d').drawImage(c,0,0);
 const actual=L.actualScenes.includes(id);qs('#context').textContent=`${String(L.number).padStart(2,'0')} · ${L.name} / ${SPECS[id].name}`;
 qs('#status').textContent=actual?'本关实际登场':'同布局风格预览 · 本关未使用此场景';qs('#status').className=actual?'actual':'study';
 qs('#stats').textContent=`${L.width} × ${L.height} 格 · 地面 ${L.floorCount} 格 · 墙体 ${L.wallCount} 格 · ${L.features.length} 个标记 · ${triggered?'机关触发状态示意':'初始状态'} · 仅素材预览`;
 qs('#outfit').textContent=SPECS[id].outfit;
 renderCompare();renderAssets();
}
function renderCompare(){
 const L=DATA.levels[selectedLevel],wrap=qs('#compare');wrap.replaceChildren();
 for(const id of Object.keys(SPECS)){
  const card=document.createElement('button');card.className='scene-card';card.type='button';
  const title=document.createElement('span');title.textContent=SPECS[id].name+(L.actualScenes.includes(id)?'':' / 风格预览');card.append(title);
  const c=renderMap(L,id,28,{grid:false,labels:false,triggered});card.append(c);card.onclick=()=>{selectedScene=id;qs('#scene').value=id;show()};wrap.append(card);
 }
}
function renderAssets(){
 const id=selectedScene,wrap=qs('#assets');wrap.replaceChildren();
 const names=[SPECS[id].plate+' / 待机',SPECS[id].plate+' / 按下',SPECS[id].timed+' / 待机',SPECS[id].timed+' / 触发',SPECS[id].box,SPECS[id].door+' / 关闭',SPECS[id].door+' / 开启',SPECS[id].inverseDoor,SPECS[id].gate+' / 可用',SPECS[id].gate+' / 用尽','47 / 正面','47 / 左侧','47 / 右侧','47 / 背面'];
 const slots=[2,3,4,5,6,7,8,9,10,11,12,13,14,15];
 slots.forEach((slot,i)=>{const div=document.createElement('div');div.className='asset';const c=canvas(116,116);drawSprite(c.getContext('2d'),id,slot,0,0,116,.91);const label=document.createElement('span');label.textContent=names[i];div.append(c,label);wrap.append(div);});
}
function startUI(){
 qs('#level').innerHTML=DATA.levels.map(l=>`<option value="${l.id}">${String(l.number).padStart(2,'0')} · ${l.name}</option>`).join('');qs('#level').value=selectedLevel;
 qs('#scene').innerHTML=Object.entries(SPECS).map(([id,s])=>`<option value="${id}">${s.name}</option>`).join('');
 qs('#level').onchange=e=>{selectedLevel=+e.target.value;show()};qs('#scene').onchange=e=>{selectedScene=e.target.value;show()};
 qs('#view').onchange=e=>{view=e.target.value;show()};qs('#facing').onchange=e=>{facing=e.target.value;show()};
 for(const [id,setter] of [['grid',v=>grid=v],['labels',v=>labels=v],['triggered',v=>triggered=v]])qs('#'+id).onchange=e=>{setter(e.target.checked);show()};
 qs('#map').onmousemove=e=>{const L=DATA.levels[selectedLevel],r=e.target.getBoundingClientRect(),px=(e.clientX-r.left)*e.target.width/r.width,py=(e.clientY-r.top)*e.target.height/r.height,x=Math.floor((px-30)/TILE),y=Math.floor((py-30)/TILE);if(x<0||y<0||x>=L.width||y>=L.height)return;const f=L.features.find(f=>f.x===x&&f.y===y),s=SPECS[selectedScene];qs('#cell').textContent=`(${x}, ${y}) · ${L.map[y][x]} · ${f?(s[f.type]||{start:'47 出发点',exit:selectedScene==='station'?'出口':'出口未开放'}[f.type]||f.type):(L.terrain[y][x]?'地面':'不可走的墙体')}`};
 show();qs('#loading').hidden=true;window.previewReady=true;
}
loadArt().then(startUI).catch(e=>{qs('#loading').textContent='素材未能加载：'+e.message;console.error(e)});
