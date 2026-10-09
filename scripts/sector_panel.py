"""Animated current and completed custom sector statistics."""
from pathlib import Path
from functools import lru_cache
import csv
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from telemetry import STUDY, t as TIME, distance as DISTANCE, power as POWER, hr as HEART
from drawing import FONT
SECTORS = STUDY['sectors']
WHITE = (255,255,255,255)
GRAY = (196,198,198,255)
BLUE = (0,135,183,175)
DARK = (35,40,46,110)
RED = (255,0,8,255)
YELLOW = (249,216,22,255)
WIDTH, HEADER, ROW, ACTIVE = 294,29,35,125

@lru_cache(maxsize=80)
def font(size, q):
    return ImageFont.truetype(str(FONT), round(size*q))

def timer(seconds):
    total = max(0,int(seconds))
    return f'{total//60}:{total%60:02d}'

def active_index(elapsed):
    return next((i for i,s in enumerate(SECTORS) if elapsed<s['end_s']),len(SECTORS)-1)

@lru_cache(maxsize=8192)
def average(index, completed_second, field):
    s = SECTORS[index]
    end = min(s['end_s'],completed_second)
    if end<=s['start_s']:
        return None
    weights = np.maximum(0,np.minimum(end,TIME[1:])-np.maximum(s['start_s'],TIME[:-1]))
    values = POWER if field=='power' else HEART
    return float(np.sum(values[1:]*weights)/(end-s['start_s']))

class Canvas:
    def __init__(self,height,scale):
        self.q = 2*scale
        self.im = Image.new('RGBA',(WIDTH*self.q,round(height*self.q)))
        self.d = ImageDraw.Draw(self.im)
    def rect(self,box,fill,radius=0):
        self.d.rounded_rectangle(tuple(round(v*self.q) for v in box),radius=round(radius*self.q),fill=fill)
    def text(self,x,y,text,size=20,color=WHITE,anchor='lt'):
        self.d.text((round(x*self.q),round(y*self.q)),str(text),font=font(size,self.q),fill=color,anchor=anchor)
    def line(self,pts,color=WHITE,width=1.5):
        self.d.line([(round(x*self.q),round(y*self.q)) for x,y in pts],fill=color,width=max(1,round(width*self.q)))
    def heart(self,x,y,size):
        pts=[]
        for i in range(81):
            t=2*math.pi*i/80
            xx=16*math.sin(t)**3
            yy=13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)
            pts.append(((x+size*(xx+16)/32)*self.q,(y+size*(13-yy)/30)*self.q))
        self.d.polygon(pts,fill=RED)
    def bolt(self,x,y,size):
        pts=[(.54,0),(.10,.56),(.44,.56),(.30,1),(.89,.35),(.56,.39),(.70,0)]
        self.d.polygon([((x+a*size)*self.q,(y+b*size)*self.q) for a,b in pts],fill=YELLOW)
    def watch(self,x,y,size=26):
        q=self.q
        self.d.ellipse((round(x*q),round((y+size*.19)*q),round((x+size*.84)*q),round((y+size)*q)),outline=WHITE,width=round(2.5*q))
        self.line([(x+size*.29,y+.4),(x+size*.54,y+.4)],width=2.6)
        self.line([(x+size*.42,y+.4),(x+size*.42,y+size*.13)],width=1.4)
        self.line([(x+size*.42,y+size*.59),(x+size*.60,y+size*.34)],width=2.2)
        self.line([(x+size*.73,y+size*.18),(x+size*.81,y+size*.10)],width=2)

def draw_row(c,y,index,completed):
    c.rect((0,y,WIDTH,y+ROW),DARK)
    s=SECTORS[index]
    c.text(15,y+8,index+1,20,GRAY)
    if completed:
        c.heart(66,y+9,23)
        c.text(92,y+9,round(s['avg_hr_bpm']),19,GRAY)
        c.bolt(152,y+8,18)
        c.text(174,y+9,round(s['avg_power_w']),19,GRAY)
        c.text(280,y+9,timer(round(s['duration_s'])),19,GRAY,'rt')
    else:
        length=s['end_m']-s['start_m']
        text=f'{length/1000:.2f}km' if length>=500 else f'{length:.0f}m'
        c.text(66,y+8,text,20,GRAY)
        c.text(280,y+8,'-:--',20,GRAY,'rt')

def draw_active(c,y,index,elapsed):
    s=SECTORS[index]
    c.rect((0,y,WIDTH,y+ACTIVE),BLUE)
    c.text(15,y+10,index+1,20)
    hr=average(index,math.floor(elapsed),'heart')
    power=average(index,math.floor(elapsed),'power')
    c.text(133,y+11,'--' if hr is None else round(hr),34,anchor='rt')
    c.heart(144,y+11,14)
    c.text(150,y+27,'AVG',12,anchor='mt')
    c.text(254,y+11,'--' if power is None else round(power),34,anchor='rt')
    c.bolt(264,y+11,13)
    c.text(268,y+27,'AVG',12,anchor='mt')
    dt=elapsed-s['start_s']
    label=timer(dt) if dt>=1 else '-:--'
    c.text(280,y+70,label,34,anchor='rt')
    tw=c.d.textlength(label,font=font(34,c.q))/c.q
    c.watch(280-tw-31,y+69,27)
    c.rect((15,y+107,280,y+121),(39,42,43,255),7)
    distance=float(np.interp(elapsed,TIME,DISTANCE))
    progress=max(0,min(1,(distance-s['start_m'])/(s['end_m']-s['start_m'])))
    if progress>0:
        mask=Image.new('L',c.im.size)
        d=ImageDraw.Draw(mask)
        d.rounded_rectangle(tuple(round(v*c.q) for v in (15,y+107,280,y+121)),radius=round(7*c.q),fill=255)
        d.rectangle((round((15+265*progress)*c.q),round((y+107)*c.q),round(281*c.q),round((y+122)*c.q)),fill=0)
        fill=Image.new('RGBA',c.im.size,WHITE)
        fill.putalpha(mask)
        c.im.alpha_composite(fill)

def render_panel(elapsed:float,scale:int=1):
    """Return transparent RGBA panel in caller's scale; place at (21,287)."""
    current=active_index(elapsed)
    dt=elapsed-SECTORS[current]['start_s']
    folded=current>0 and dt<5/60
    height=HEADER+(ROW if current else 0)+(ROW if folded else ACTIVE)+ROW*(len(SECTORS)-1-current)
    c=Canvas(height,scale)
    c.rect((0,0,WIDTH,HEADER),WHITE,9)
    c.rect((0,HEADER/2,WIDTH,HEADER),WHITE)
    c.text(WIDTH/2,5,'Sector Stats',21,(33,34,34,255),'mt')
    y=HEADER
    if current:
        draw_row(c,y,current-1,True)
        y+=ROW
    if folded:
        draw_row(c,y,current,False)
        y+=ROW
    else:
        draw_active(c,y,current,elapsed)
        y+=ACTIVE
    for i in range(current+1,len(SECTORS)):
        draw_row(c,y,i,False)
        y+=ROW
    return c.im.resize((WIDTH*scale,round(height*scale)),Image.Resampling.LANCZOS)
