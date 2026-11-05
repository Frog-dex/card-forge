/* Card Forge — shared helpers: load the deck plan + faction manifest, and compose a
   finished card (interior, art, border, corner marbles, guides) on a <canvas>.
   No dependencies. Exposes window.Forge. */
(function(){
  "use strict";
  const CW=1650, CH=2250, BLEED=75, BORDER=44;
  const TRIM=[BLEED,BLEED,CW-BLEED,CH-BLEED];          // 2.5 x 3.5 in @ 600 DPI
  const SAFE=[150,150,CW-150,CH-150];
  const WIN=[BLEED+BORDER,BLEED+BORDER,CW-BLEED-BORDER,CH-BLEED-BORDER];
  const MARBLE_D=286, MARBLE_OFF=BLEED+5;                 // matches corner_badges.py

  const params=new URLSearchParams(location.search);
  // Where line-art cutouts (card-NN.png) live. Override with ?art=path/ — remembered per browser.
  function artDir(){
    let d=params.get("art");
    try{ if(d) localStorage.setItem("forge.art",d); else d=localStorage.getItem("forge.art"); }catch(e){ /* storage blocked */ }
    d=d||"sample-art/";
    return d.endsWith("/")?d:d+"/";
  }

  const cache=new Map();
  function img(src){
    if(!cache.has(src)) cache.set(src,new Promise(res=>{
      const i=new Image(); i.decoding="async";
      i.onload=()=>res(i); i.onerror=()=>res(null); i.src=src;
    }));
    return cache.get(src);
  }

  let dataP=null;
  function load(){
    if(!dataP) dataP=Promise.all([
      fetch("plan.json").then(r=>r.json()),
      fetch("borders/borders_manifest.json").then(r=>r.json()),
    ]).then(([plan,manifest])=>{
      const factions=plan.cols.map(k=>{
        const m=manifest.elements[k]||{}; const [el,animal]=(m.name||k).split(" - ");
        return {key:k,name:el,animal:animal||"",hex:m.hex||"#888"};
      });
      return {plan,manifest,factions};
    });
    return dataP;
  }

  const pad2=n=>String(n).padStart(2,"0");
  const urls={
    border:k=>"borders/border_"+k+".png",
    emblem:k=>"elements/emblem_"+k+".png",
    symbol:k=>"elements/symbol_"+k+".png",
    marble:(n,slot)=>"marbles/"+pad2(n)+"_"+slot+".png",
    guides:()=>"borders/guides.png",
  };

  // Line-art cutout -> solid single-color ink (alpha threshold), cached per (img,color,thr).
  const inkCache=new WeakMap();
  function ink(im,rgb,thr){
    let per=inkCache.get(im); if(!per){per=new Map();inkCache.set(im,per);}
    const key=rgb.join(",")+"|"+thr; if(per.has(key)) return per.get(key);
    const c=document.createElement("canvas"); c.width=im.naturalWidth||im.width; c.height=im.naturalHeight||im.height;
    const x=c.getContext("2d"); x.drawImage(im,0,0);
    const d=x.getImageData(0,0,c.width,c.height), p=d.data;
    for(let i=0;i<p.length;i+=4){ if(p[i+3]>thr){p[i]=rgb[0];p[i+1]=rgb[1];p[i+2]=rgb[2];p[i+3]=255;} else p[i+3]=0; }
    x.putImageData(d,0,0); per.set(key,c); return c;
  }
  function hexRGB(h){h=h.replace("#","");return [0,2,4].map(i=>parseInt(h.slice(i,i+2),16));}

  function roundRect(x,X,Y,W,H,r){x.beginPath();x.moveTo(X+r,Y);x.arcTo(X+W,Y,X+W,Y+H,r);
    x.arcTo(X+W,Y+H,X,Y+H,r);x.arcTo(X,Y+H,X,Y,r);x.arcTo(X,Y,X+W,Y,r);x.closePath();}

  /* Compose one card at full print resolution into an offscreen canvas, then draw it scaled
     into `canvas`. opts: mode "dark"|"light", guides bool, trim bool (crop bleed), thin (ink threshold),
     placeholder bool (faint element glyph when the art isn't bundled), round bool (round the preview corners;
     pass false for print exports). Returns {hasArt}. */
  async function drawCard(canvas,cell,opts={}){
    const o=Object.assign({mode:"dark",guides:false,trim:false,thin:110,placeholder:true,round:true},opts);
    const elem=cell.element, card=cell.card||"";
    const isEmb=card.startsWith("element-");
    const artSrc=isEmb?urls.emblem(card.slice(8)):(card?artDir()+card+".png":null);
    const [bd,mt,mb,art,sym,gd]=await Promise.all([
      img(urls.border(elem)),img(urls.marble(cell.num,"top")),img(urls.marble(cell.num,"bot")),
      artSrc?img(artSrc):null, img(urls.symbol(elem)), o.guides?img(urls.guides()):null]);

    const full=document.createElement("canvas"); full.width=CW; full.height=CH;
    const x=full.getContext("2d");
    x.fillStyle=isEmb?"#141418":(o.mode==="light"?"#ffffff":"#18181c");
    x.fillRect(0,0,CW,CH);

    if(art && cell.art){
      const a=cell.art;
      if(isEmb) x.drawImage(art,a.x,a.y,a.w,a.h);
      else x.drawImage(ink(art,o.mode==="light"?[18,18,18]:[242,242,242],o.thin),a.x,a.y,a.w,a.h);
    }else if(o.placeholder && sym && !isEmb){
      // faint element glyph so unbundled art reads as an intentional "art slot"
      const s=Math.min(WIN[2]-WIN[0],WIN[3]-WIN[1])*0.42, cx=CW/2, cy=CH/2;
      const sc=s/Math.max(sym.width,sym.height), w=sym.width*sc, h=sym.height*sc;
      const tint=ink(sym,hexRGB(cell.hex||"#888888"),20);
      x.globalAlpha=card?0.22:0.12; x.drawImage(tint,cx-w/2,cy-h/2,w,h); x.globalAlpha=1;
    }
    if(bd) x.drawImage(bd,0,0,CW,CH);
    if(mt) x.drawImage(mt,MARBLE_OFF,MARBLE_OFF,MARBLE_D,MARBLE_D);
    if(mb) x.drawImage(mb,CW-MARBLE_OFF-MARBLE_D,CH-MARBLE_OFF-MARBLE_D,MARBLE_D,MARBLE_D);
    if(gd) x.drawImage(gd,0,0,CW,CH);

    const src=o.trim?TRIM:[0,0,CW,CH], sw=src[2]-src[0], sh=src[3]-src[1];
    const ctx=canvas.getContext("2d");
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.imageSmoothingQuality="high";
    ctx.save(); if(o.round){ roundRect(ctx,0,0,canvas.width,canvas.height,canvas.width*(o.trim?0.056:0.045)); ctx.clip(); }
    ctx.drawImage(full,src[0],src[1],sw,sh,0,0,canvas.width,canvas.height);
    ctx.restore();
    return {hasArt:!!(art&&cell.art)};
  }

  window.Forge={CW,CH,BLEED,BORDER,TRIM,SAFE,WIN,MARBLE_D,load,img,urls,drawCard,ink,hexRGB,pad2,artDir};
})();
