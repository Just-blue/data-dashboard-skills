from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os
FONT = Path(os.environ.get("HUD_FONT", str(Path(__file__).resolve().parent.parent / "assets/Tektur-Medium.ttf")))
C = {"font_"+k: str(FONT) for k in ["bold", "regular", "cjk"]}
WHITE=(255,255,255,255);MUTED=(216,225,233,255);BG=(40,49,61,210);ORANGE=(255,103,25,255)
ZCOL=['#aaaeb5','#299be8','#31b36b','#f2d04c','#ee873c','#e84548','#9e52b1']
@lru_cache(maxsize=300)
def font(kind,size,scale):return ImageFont.truetype(C['font_'+kind],round(size*scale))
class Canvas:
 def __init__(self,w=1920,h=1080,scale=1):self.s=scale;self.im=Image.new('RGBA',(round(w*scale),round(h*scale)));self.d=ImageDraw.Draw(self.im)
 def box(self,b,c,r=0):
  q=tuple(round(v*self.s) for v in b)
  if r:self.d.rounded_rectangle(q,round(r*self.s),fill=c)
  else:self.d.rectangle(q,fill=c)
 def line(self,pts,c,w=1):self.d.line([(round(x*self.s),round(y*self.s)) for x,y in pts],fill=c,width=max(1,round(w*self.s)),joint='curve')
 def poly(self,pts,c):self.d.polygon([(round(x*self.s),round(y*self.s)) for x,y in pts],fill=c)
 def text(self,x,y,text,size=18,c=WHITE,kind='regular',anchor='lt'):self.d.text((round(x*self.s),round(y*self.s)),str(text),fill=c,font=font(kind,size,self.s),anchor=anchor)
 def circle(self,x,y,r,c,outline=None,w=1):self.d.ellipse(((x-r)*self.s,(y-r)*self.s,(x+r)*self.s,(y+r)*self.s),fill=c,outline=outline,width=max(1,round(w*self.s)))
 def icon(self,kind,x,y,size=22,c=WHITE):
  s=size/24
  def pt(a,b):return x+a*s,y+b*s
  if kind=='bolt':self.poly([pt(7,0),pt(19,0),pt(13,10),pt(20,10),pt(6,26),pt(9,14),pt(3,14)],c)
  elif kind=='heart':
   self.circle(*pt(7,8),6*s,c);self.circle(*pt(17,8),6*s,c);self.poly([pt(1,9),pt(23,9),pt(12,24)],c)
   self.line([pt(2,12),pt(7,12),pt(10,8),pt(13,16),pt(16,12),pt(22,12)],BG,2*s)
  elif kind in ['clock','cadence']:
   self.circle(*pt(12,12),10*s,None,c,2*s)
   self.line([pt(12,4),pt(12,12),pt(18,15)],c,2*s)
   if kind=='cadence':self.line([pt(3,22),pt(20,2)],c,3*s)
  elif kind=='mountain':
   self.poly([pt(0,22),pt(10,3),pt(15,12),pt(18,8),pt(26,22)],c)
   self.poly([pt(7,11),pt(10,6),pt(13,11)],BG)
  elif kind=='route':self.line([pt(2,20),pt(9,4),pt(15,20),pt(22,4)],c,2*s)
  elif kind=='flag':
   self.line([pt(1,0),pt(1,25)],c,2*s)
   for a in range(4):
    for b in range(3):self.box((x+(3+a*5)*s,y+b*5*s,x+(8+a*5)*s,y+(b+1)*5*s),WHITE if (a+b)%2==0 else (42,50,60,255))
  elif kind=='pin':
   self.circle(*pt(12,8),7*s,c);self.poly([pt(6,11),pt(18,11),pt(12,24)],c);self.circle(*pt(12,8),3*s,BG)
  elif kind=='energy':self.poly([pt(13,0),pt(22,13),pt(20,20),pt(12,25),pt(4,21),pt(2,13),pt(7,4),pt(8,13)],c)
