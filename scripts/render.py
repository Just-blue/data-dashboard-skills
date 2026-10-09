from pathlib import Path
from functools import lru_cache
import importlib.util
import json
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import telemetry as hud
from telemetry import CONFIG, STUDY
from expanded_map import render_map
from sector_panel import render_panel

BG = (40, 46, 58, 185)
WHITE = (255,255,255,255)
GRAY = (194,205,215,255)
ORANGE = (255,93,0,255)
ZONES = [(184,187,190,210),(0,144,206,210),(53,187,104,210),(244,207,44,210),(245,128,34,210),(234,57,48,210),(163,77,168,210)]


def zone(power):
    return int(np.searchsorted([.55,.75,.90,1.05,1.20,1.50],power/hud.C['ftp_account_w']))


def gauge(cv,x,y,size):
    s=cv.s
    cv.d.arc((round(x*s),round(y*s),round((x+size)*s),round((y+size)*s)),185,355,fill=WHITE,width=max(1,round(2*s)))
    cv.line([(x+size*.5,y+size*.64),(x+size*.77,y+size*.15)],WHITE,2)


def power_tile(cv, ts):
    a=hud.stats(ts)
    x,y=21,25
    cv.box((x,y,x+294,y+202),BG,12)
    cv.icon('bolt',x+23,y+15,38,WHITE if zone(a['power_3s_w'])==0 else ZONES[zone(a['power_3s_w'])])
    value=str(a['power_3s_w'])
    cv.text(x+241,y+11,value,66,kind='bold',anchor='rt')
    cv.text(x+242,y+35,'W',31,kind='bold')
    samples=hud.power[(hud.t>hud.START)&(hud.t<=ts)]
    counts=np.histogram(samples/hud.C['ftp_account_w'],[0,.55,.75,.90,1.05,1.20,1.5,np.inf])[0]
    xx=x
    for n,color in zip(counts,ZONES):
        end=xx+294*n/max(1,sum(counts))
        if end>xx:cv.box((xx,y+70,end,y+83),color)
        xx=end
    entries=[(x+23,y+96,'cadence',a['cadence_rpm'],'RPM'),(x+173,y+96,'heart',a['heart_rate_bpm'],'BPM'),(x+23,y+151,'bolt',a['split_avg_power_w'],'AVG'),(x+173,y+151,'energy',a['segment_work_kj'],'KJ')]
    for xx,yy,icon,value,label in entries:
        cv.icon(icon,xx,yy+4,25)
        cv.text(xx+53,yy-5,value,35,kind='bold')
        cv.text(xx+63,yy+28,label,18)


def center_tile(cv,elapsed,ts):
    a=hud.stats(ts)
    x,y,w,h=635,25,646,150
    cv.box((x,y,x+w,y+h),BG,12)
    # Keep every item in the header aligned while increasing its top inset by 11 px.
    y+=11
    cv.text(x+83,y+1,round(a['speed_kmh']),53,kind='bold',anchor='rt')
    gauge(cv,x+88,y+6,18)
    cv.text(x+89,y+29,'KM/H',17)
    cv.text(x+263,y+1,f"{a['segment_distance_m']/1000:.1f}",53,kind='bold',anchor='rt')
    cv.icon('route',x+267,y+9,20)
    cv.text(x+267,y+29,'KM',17)
    cv.text(x+419,y+1,a['segment_ascent_m'],53,kind='bold',anchor='rt')
    cv.icon('mountain',x+423,y+10,18)
    cv.text(x+424,y+29,'M',17)
    cv.text(x+610,y+1,f'{int(elapsed)//60}:{int(elapsed)%60:02d}',53,kind='bold',anchor='rt')
    cv.icon('clock',x+615,y+7,19)
    cv.text(x+617,y+29,'ET',16)
    cv.box((x+9,y+50,x+w-9,y+56),(181,190,198,230),3)
    progress=a['segment_distance_m']/(hud.de-hud.ds)
    cv.box((x+9,y+50,x+9+(w-18)*progress,y+56),ORANGE,3)
    # Reference account badges use actual course metadata instead of invented game balances.
    cv.box((x+9,y+62,x+130,y+85),(29,37,46,210),11)
    cv.text(x+21,y+65,f'{len(STUDY["sectors"])} SECTORS',17)
    cv.box((x+w-137,y+62,x+w-9,y+85),(24,181,220,230),11)
    cv.icon('mountain',x+w-128,y+66,15)
    cv.text(x+w-17,y+64,f'{round(hud.ascent[-1]-hud.ascent[0])} M',20,anchor='rt')
    # Checker icon, course label and current course time match the recording's lower row.
    for i in range(4):
        for j in range(5):
            if (i+j)%2==0:cv.box((x+29+i*4,y+102+j*4,x+31+i*4,y+104+j*4),(36,139,143,245))
    label = CONFIG['route_display_name']
    label_size = 23
    while label_size > 12 and cv.d.textlength(label,font=hud.font('regular',label_size,cv.s))/cv.s > 165:
        label_size -= 1
    while cv.d.textlength(label,font=hud.font('regular',label_size,cv.s))/cv.s > 165:
        label = label[:-2]+'…'
    cv.text(x+58,y+101,label,label_size)
    cv.text(x+235,y+101,f'{int(elapsed)//60}:{int(elapsed)%60:02d}',23)


def slope_profile(cv,ts):
    x,y,w,h=635,184,646,124
    cv.box((x,y,x+w,y+h),BG,7)
    cv.text(x+13,y+9,'CLIMB PROFILE',13,c=GRAY)
    distance=hud.val(hud.distance,ts)
    left=max(hud.ds,distance-160)
    right=min(hud.de,left+800)
    left=max(hud.ds,right-800)
    ds=np.linspace(left,right,161)
    zs=np.interp(ds,hud.grid,hud.zs)
    low=float(min(zs))-4
    high=float(max(zs))+8
    base_y=y+104
    def project(d,z):
        return x+12+(d-left)/(right-left)*(w-24),base_y-(z-low)/(high-low)*75
    points=[project(d,z) for d,z in zip(ds,zs)]
    for i in range(len(points)-1):
        grade=(zs[i+1]-zs[i])/(ds[i+1]-ds[i])*100
        cv.poly([points[i],points[i+1],(points[i+1][0],base_y),(points[i][0],base_y)],hud.slope_color(grade))
    cv.line(points,(255,255,255,185),1)
    px,py=project(distance,float(np.interp(distance,hud.grid,hud.zs)))
    cv.line([(px,y+41),(px,base_y)],WHITE,1.5)
    cv.circle(px,py,3.5,ORANGE,WHITE,1)
    grade=hud.stats(ts)['grade_estimated_percent']
    label_x=max(x+60,min(x+w-60,px))
    cv.box((label_x-32,y+20,label_x+32,y+43),WHITE,4)
    cv.text(label_x,y+22,f'{grade:.1f}%',18,c=(26,34,43,255),anchor='mt')
    cv.text(x+13,y+108,f'{(left-hud.ds)/1000:.2f} KM',11,c=GRAY)
    cv.text(x+w-13,y+108,f'{(right-hud.ds)/1000:.2f} KM',11,c=GRAY,anchor='rt')


def history(cv,ts):
    left,right,top,bottom=20,1582,993,1079
    end=math.floor(ts)
    start=max(hud.START,end-600)
    elapsed=ts-hud.START
    if elapsed<=0:
        return
    if elapsed<600:
        right=left+(right-left)*elapsed/600
    xs=np.linspace(start,ts,max(2,round(780*min(1,elapsed/600))))
    powers=np.interp(xs,hud.t,hud.power)
    hrs=np.interp(xs,hud.t,hud.hr)
    py=bottom-np.clip(powers/500,0,1)*80
    for i in range(len(xs)-1):
        x1=left+(right-left)*i/(len(xs)-1);x2=left+(right-left)*(i+1)/(len(xs)-1)
        c=ZONES[zone(powers[i])]
        cv.poly([(x1,bottom),(x1,py[i]),(x2,py[i+1]),(x2,bottom)],(*c[:3],145))
    outline=[(left+(right-left)*i/(len(xs)-1),py[i]) for i in range(len(xs))]
    cv.line(outline,(176,188,198,150),.8)
    line=[(left+(right-left)*i/(len(xs)-1),bottom-np.clip((hr-90)/110,0,1)*95) for i,hr in enumerate(hrs)]
    cv.line(line,(209,55,48,210),1)


def rider_tile(cv,ts):
    x,y,w=1612,767,294
    cv.box((x,y,x+w,y+28),WHITE,7)
    cv.box((x,y+20,x+w,y+28),WHITE)
    cv.text(x+w/2,y+5,'Rider',19,c=(24,27,29,255),anchor='mt')
    cv.box((x,y+28,x+w,y+81),(0,142,192,237),4)
    cv.text(x+w-15,y+33,CONFIG['rider_name'],23,anchor='rt')
    a=hud.stats(ts)
    cv.text(x+142,y+60,f'{rider_power_ratio(ts):.1f} w/kg',19,c=(161,223,245,255),anchor='rt')
    cv.text(x+w-15,y+60,f"{a['segment_distance_m']/1000:.1f} KM",19,c=(161,223,245,255),anchor='rt')
    cv.box((x,y+87,x+w,y+114),(157,170,182,65),5)


def rider_power_ratio(ts):
    index=int(np.searchsorted(hud.t,ts,side='right')-1)
    sample_t=hud.t[index]
    samples=hud.power[(hud.t>=max(hud.START,sample_t-2))&(hud.t<=sample_t)]
    return float(np.nanmean(samples))/CONFIG['rider_weight_kg']


def render(elapsed):
    cv=hud.Canvas()
    ts=hud.START+elapsed
    power_tile(cv,ts)
    center_tile(cv,elapsed,ts)
    slope_profile(cv,ts)
    # Inactive power-up ring is part of the user-supplied HUD layout.
    cv.circle(490,117,79,None,(178,188,218,48),10)
    cv.im.alpha_composite(render_panel(elapsed),(21,287))
    map_image=render_map(elapsed,2).resize((294,736),Image.Resampling.LANCZOS)
    cv.im.alpha_composite(map_image,(1612,25))
    rider_tile(cv,ts)
    history(cv,ts)
    return cv.im
