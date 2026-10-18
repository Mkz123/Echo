// Optional maintenance utility; requires Playwright. The preview itself needs no dependencies.
const {chromium}=require('playwright');const fs=require('fs'),path=require('path'),crypto=require('crypto');
(async()=>{
const root=path.resolve(__dirname,'..');
const browser=await chromium.launch({executablePath:process.env.ECHO_CHROME_PATH||(process.platform==='darwin'?'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome':undefined),headless:true,args:['--no-sandbox']});
const context=await browser.newContext({viewport:{width:1440,height:1080},deviceScaleFactor:1,offline:true});const page=await context.newPage();const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});
await page.goto('file://'+root+'/preview.html');await page.waitForFunction(()=>window.previewReady,{},{timeout:30000});
const save=(file,b64)=>{fs.mkdirSync(path.dirname(path.join(root,file)),{recursive:true});fs.writeFileSync(path.join(root,file),Buffer.from(b64,'base64'))};
const atlasAudit=await page.evaluate(()=>Object.keys(SPECS).map(id=>({id,width:bitmaps[id].naturalWidth,height:bitmaps[id].naturalHeight,directions:{front:12,left:actualSlot(id,13),right:actualSlot(id,14),back:15},bounds:spriteBounds[id]})));
console.log('Direction source slots:',atlasAudit.map(a=>({id:a.id,left:a.directions.left,right:a.directions.right})));
for(const a of atlasAudit){if(a.directions.left===a.directions.right)throw Error('Direction conflict');}
fs.writeFileSync(path.join(root,'atlas-metadata.json'),JSON.stringify(atlasAudit,null,2));
const audit=[];
for(let n=0;n<15;n++){
for(const id of ['greenhouse','workshop','lab','bridge','station']){
const r=await page.evaluate(({n,id})=>{
 const L=DATA.levels[n],background=renderMap(L,id,64,{layer:'background',grid:false,labels:false,robot:false}),composite=renderMap(L,id,64,{grid:true,labels:true});
 const fromStrings=L.map.map(row=>[...row].map(ch=>ch!=='#'));
 if(JSON.stringify(background.layoutMask)!==JSON.stringify(fromStrings))throw Error('Background layout mismatch '+L.name+' / '+id);
 if(JSON.stringify(composite.layoutMask)!==JSON.stringify(fromStrings))throw Error('Composite layout mismatch');
 for(const f of L.features)if(!fromStrings[f.y][f.x])throw Error('Feature placed on wall');
 return {background:background.toDataURL('image/png').split(',')[1],composite:composite.toDataURL('image/png').split(',')[1],mask:background.layoutMask,features:L.features,actual:L.actualScenes.includes(id),number:L.number,name:L.name};
},{n,id});
const prefix=String(n+1).padStart(2,'0');save(`maps/${id}/${prefix}-background.png`,r.background);save(`maps/${id}/${prefix}-preview.png`,r.composite);
audit.push({level:n+1,name:r.name,scene:id,actual:r.actual,maskHash:crypto.createHash('sha256').update(JSON.stringify(r.mask)).digest('hex'),featuresHash:crypto.createHash('sha256').update(JSON.stringify(r.features)).digest('hex'),floorCells:r.mask.flat().filter(Boolean).length,featureCount:r.features.length,pass:true});
}
const mask=await page.evaluate(n=>{const L=DATA.levels[n],c=canvas(L.width*32,L.height*32),g=c.getContext('2d');for(let y=0;y<L.height;y++)for(let x=0;x<L.width;x++){g.fillStyle=L.map[y][x]==='#'?'#000':'#fff';g.fillRect(x*32,y*32,32,32);}return c.toDataURL('image/png').split(',')[1]},n);save(`masks/${String(n+1).padStart(2,'0')}-terrain.png`,mask);
if(n%3===0)console.log('Exported levels',n+1,'/15');
}
for(let n=1;n<=15;n++){const group=audit.filter(a=>a.level===n);if(new Set(group.map(a=>a.maskHash)).size!==1||new Set(group.map(a=>a.featuresHash)).size!==1)throw Error('Cross-scene coordinate mismatch '+n);}
for(const id of ['greenhouse','workshop','lab','bridge','station'])for(let slot=0;slot<16;slot++){
 const r=await page.evaluate(({id,slot})=>{const size=slot>=12?192:128,c=canvas(size,size),g=c.getContext('2d');if(slot<2)tile(g,id,slot===0,0,0,size);else drawSprite(g,id,slot,0,0,size,.91);return {data:c.toDataURL('image/png').split(',')[1],name:SLOT_NAMES[slot]}},{id,slot});save(`sprites/${id}/${r.name}.png`,r.data);
}
const boards=await page.evaluate(()=>{
 function heading(g,s,x,y,size=22){g.fillStyle='#e9e7d0';g.font=`600 ${size}px ${FONT}`;g.textAlign='left';g.textBaseline='middle';g.fillText(s,x,y)}
 const ids=Object.keys(SPECS),L=DATA.levels[13];
 const overview=canvas(1590,1900),g=overview.getContext('2d');g.fillStyle='#11281f';g.fillRect(0,0,overview.width,overview.height);heading(g,'ECHO / 同一关 · 五种记忆',32,38,30);heading(g,'第 14 关「所有的磁带」 · 坐标与机关位置一致 · 仅素材预览',32,78,16);
 ids.forEach((id,i)=>{const col=i%2,row=Math.floor(i/2),x=30+col*780,y=115+row*585;g.fillStyle='#1d3c2c';g.fillRect(x,y,755,565);heading(g,SPECS[id].name,x+18,y+26);const m=renderMap(L,id,48,{labels:true,grid:true});g.drawImage(m,x+17,y+52,720,528);});
 heading(g,'纯地面、墙体、道具、角色分别导出；背景未接入游戏。',820,1440,19);heading(g,'地形从原始字符地图逐格铺设，墙体装饰不会侵入可走格。',820,1480,16);heading(g,'15 关 × 5 场景 = 75 组；实际登场组合 36 组。',820,1520,16);
 const robots=canvas(1120,1220),r=robots.getContext('2d');r.fillStyle='#11281f';r.fillRect(0,0,1120,1220);heading(r,'47 / 五种着装 · 四个独立朝向',30,35,27);
 ['正面','左侧','右侧','背面'].forEach((s,j)=>heading(r,s,310+j*190,79,16));
 ids.forEach((id,i)=>{const y=105+i*218;heading(r,SPECS[id].name,25,y+70,19);r.fillStyle='#9ab59b';r.font=`12px ${FONT}`;r.fillText(SPECS[id].outfit.split(' · ').slice(0,2).join(' / '),25,y+100);[12,13,14,15].forEach((slot,j)=>drawSprite(r,id,slot,255+j*195,y,190,.94));});
 const props=canvas(1450,1040),p=props.getContext('2d');p.fillStyle='#11281f';p.fillRect(0,0,1450,1040);heading(p,'场景道具 / 状态提案',30,34,27);
 const slots=[2,3,4,5,6,7,8,9,10,11],titles=['按钮 待机','按钮 按下','定时 待机','定时 触发','可推箱','门 关闭','门 开启','反向门','闸机 可用','闸机 用尽'];titles.forEach((s,j)=>heading(p,s,182+j*124,78,12));
 ids.forEach((id,i)=>{const y=110+i*181;heading(p,SPECS[id].name,22,y+55,19);p.fillStyle='#a2bca0';p.font=`12px ${FONT}`;p.fillText(SPECS[id].plate,22,y+87);p.fillText(SPECS[id].box,22,y+107);slots.forEach((slot,j)=>drawSprite(p,id,slot,163+j*124,y,120,.93));});
 return {overview:overview.toDataURL('image/png').split(',')[1],robots:robots.toDataURL('image/png').split(',')[1],props:props.toDataURL('image/png').split(',')[1]};
});
save('review/scene-overview.png',boards.overview);save('review/robot-turnarounds.png',boards.robots);save('review/prop-states.png',boards.props);
await page.screenshot({path:path.join(root,'review/preview-desktop.png'),fullPage:true});
await page.selectOption('#level','4');await page.selectOption('#scene','lab');await page.selectOption('#view','mask');await page.selectOption('#facing','back');await page.check('#triggered');await page.screenshot({path:path.join(root,'review/grid-check.png')});
await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(root,'review/preview-mobile.png'),fullPage:true});if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow');
if(errors.length||requests.length)throw Error(JSON.stringify({errors,requests}));
const report={generatedAt:new Date().toISOString(),levelCount:15,sceneCount:5,layoutCount:audit.length,actualLayoutCount:audit.filter(a=>a.actual).length,backgroundFiles:75,compositeFiles:75,terrainMasks:15,spriteFiles:80,crossSceneMasksIdentical:true,crossSceneFeaturesIdentical:true,offlineHttpRequests:requests.length,browserErrors:errors,gameIntegrated:false,cases:audit};
fs.writeFileSync(path.join(root,'validation.json'),JSON.stringify(report,null,2));console.log('PASS',JSON.stringify({...report,cases:undefined}));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
