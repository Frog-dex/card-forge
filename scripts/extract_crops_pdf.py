#!/usr/bin/env python3
"""Extract every embedded image from Spirit-Strikers-Cropped-Drawings.pdf at
NATIVE resolution -> originals/pdf/page-NN.png, and report sizes."""
import os
import fitz

PDF="/Users/blu/Library/Mobile Documents/com~apple~CloudDocs/Art/Spirit Strikers/Drawings/Spirit-Strikers-Cropped-Drawings.pdf"
OUT="/Users/blu/card-borders/poker-deck/originals/pdf"; os.makedirs(OUT,exist_ok=True)

doc=fitz.open(PDF)
print("pages:",len(doc))
sizes=[]
n=0
for pno in range(len(doc)):
    for xref,*_ in doc.get_page_images(pno):
        pix=fitz.Pixmap(doc,xref)
        if pix.n>4: pix=fitz.Pixmap(fitz.csRGB,pix)
        fn=os.path.join(OUT,f"page-{pno+1:02d}.png")
        pix.save(fn); sizes.append((pno+1,pix.width,pix.height)); n+=1
        break            # first (main) image per page
print("extracted",n,"images")
ws=[w for _,w,h in sizes]
print("min/median/max width:",min(ws),sorted(ws)[len(ws)//2],max(ws))
for p,w,h in sizes[:10]: print(f"  page {p}: {w}x{h}")
