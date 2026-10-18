function paintWholeScene(L,id,painting,unit=128){
 const W=L.width*unit,H=L.height*unit,c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');
 const p=SCENE_PALETTES[id];let seed=1729+L.number*51;const random=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 // One continuous floor plane with world-wide light and texture, never one square at a time.
 const light=g.createLinearGradient(0,H,W,0);light.addColorStop(0,p.floorDark);light.addColorStop(1,p.floorLight);g.fillStyle=light;g.fillRect(0,0,W,H);
 for(let i=0;i<W*H/95;i++){
  const x=random()*W,y=random()*H,r=.4+random()*2.4;g.fillStyle=random()>.5?'rgba(255,249,214,.12)':'rgba(47,35,24,.08)';
  g.beginPath();g.ellipse(x,y,r*2,r,-.4,0,Math.PI*2);g.fill();
 }
 for(let i=0;i<W*H/5000;i++){const x=random()*W,y=random()*H;g.strokeStyle='rgba(71,55,32,.1)';g.lineWidth=.7;g.beginPath();g.moveTo(x,y);g.lineTo(x+random()*18+3,y+random()*3-1.5);g.stroke();}
 const walls=new Path2D(),edges=new Path2D();
 const floor=(x,y)=>x>=0&&y>=0&&x<L.width&&y<L.height&&L.map[y][x]!=='#';
 for(let y=0;y<L.height;y++)for(let x=0;x<L.width;x++){
  if(!floor(x,y))walls.rect(x*unit,y*unit,unit,unit);
  else {
   if(!floor(x,y-1)){edges.moveTo(x*unit,y*unit);edges.lineTo((x+1)*unit,y*unit)}
   if(!floor(x,y+1)){edges.moveTo(x*unit,(y+1)*unit);edges.lineTo((x+1)*unit,(y+1)*unit)}
   if(!floor(x-1,y)){edges.moveTo(x*unit,y*unit);edges.lineTo(x*unit,(y+1)*unit)}
   if(!floor(x+1,y)){edges.moveTo((x+1)*unit,y*unit);edges.lineTo((x+1)*unit,(y+1)*unit)}
  }
 }
 g.save();g.clip(walls);
 // Exactly one full-frame environment illustration, with no repeated tile stamps.
 g.drawImage(painting,0,0,W,H);
 g.lineJoin='round';g.lineCap='round';g.strokeStyle='#15251f';g.lineWidth=22;g.stroke(edges);
 g.strokeStyle=p.rim;g.lineWidth=14;g.stroke(edges);
 g.strokeStyle='rgba(246,228,182,.68)';g.lineWidth=3;g.stroke(edges);
 // A scene-wide perimeter frame; it lies wholly inside the outer blocked margin.
 g.lineWidth=12;g.strokeStyle=p.frame;g.strokeRect(18,18,W-36,H-36);g.lineWidth=3;g.strokeStyle='#e5d8b2';g.strokeRect(25,25,W-50,H-50);
 for(let x=unit*.5;x<W;x+=unit*2.4){g.fillStyle=p.frame;g.fillRect(x,5,6,35);g.fillRect(x,H-40,6,35);}
 for(let y=unit*.6;y<H;y+=unit*2.4){g.fillStyle=p.frame;g.fillRect(5,y,35,6);g.fillRect(W-40,y,35,6);}
 g.restore();
 return c;
}
