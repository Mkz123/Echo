const {chromium}=require(process.env.ECHO_PLAYWRIGHT || 'playwright');
const fs=require('fs');
const root=require('path').resolve(__dirname,'..');
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1100}});
 const errors=[],external=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route(/^https?:/,r=>{external.push(r.request().url());return r.abort()});
 await page.goto('file://'+root+'/preview.html');
 await page.waitForFunction(()=>!document.getElementById('stage').classList.contains('loading'));
 const result=await page.evaluate(()=>{
  const d=JSON.parse(document.getElementById('data').textContent);
  return {levels:d.levels.length,assets:Object.keys(d.assets).length,cards:document.querySelectorAll('.card').length,scenes:d.levels.map(l=>l.actualScenes.length)};
 });
 if(result.levels!==15||result.assets!==35||result.cards!==36)throw Error('Wrong coverage '+JSON.stringify(result));
 const visited=[];
 for(let i=0;i<15;i++){
  await page.selectOption('#level',String(i));
  await page.waitForFunction(()=>!document.getElementById('stage').classList.contains('loading'));
  const buttons=page.locator('#scenes button'),n=await buttons.count();
  if(n!==result.scenes[i])throw Error('Invalid scene count '+i);
  for(let j=0;j<n;j++){
   await buttons.nth(j).click();
   await page.waitForFunction(()=>!document.getElementById('stage').classList.contains('loading'));
   visited.push(await page.locator('#title').textContent());
  }
 }
 await page.selectOption('#level','13');
 await page.locator('#scenes button').first().click();
 await page.waitForFunction(()=>!document.getElementById('stage').classList.contains('loading'));
 await page.screenshot({path:root+'/review/offline-desktop.png',fullPage:false});
 const before=await page.locator('#canvas').evaluate(c=>c.toDataURL());
 await page.check('#route');await page.check('#grid');await page.check('#features');
 const after=await page.locator('#canvas').evaluate(c=>c.toDataURL());
 if(before===after)throw Error('Inspection overlays did not draw');
 await page.screenshot({path:root+'/review/layout-overlay.png',fullPage:false});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:root+'/review/offline-mobile.png',fullPage:false});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 if(overflow||errors.length||external.length)throw Error(JSON.stringify({overflow,errors,external}));
 const report={...result,visited:visited.length,offline:true,externalRequests:external.length,pageErrors:errors,mobileOverflow:overflow,overlaysChangeImage:true};
 fs.writeFileSync(root+'/review/verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
