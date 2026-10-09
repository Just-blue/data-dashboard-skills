"""Recorded Alpe expanded-map layout with the configured segment telemetry."""
from pathlib import Path
from functools import lru_cache
import importlib.util
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import telemetry as hud
from telemetry import CONFIG, STUDY
SECTORS = STUDY['sectors']
from drawing import FONT as SPRINT
CJK = SPRINT
ORANGE = (255, 92, 22, 255)
WHITE = (255, 255, 255, 255)
BLUE = (0, 155, 233, 255)
ACTUAL_HEADING = np.unwrap(np.arctan2(np.gradient(hud.x),np.gradient(hud.y)))

@lru_cache(maxsize=100)
def font(size, scale, cjk=False):
    return ImageFont.truetype(str(CJK if cjk else SPRINT), round(size * scale))


def star_points(cx, cy, radius):
    return [(cx + math.sin(k * math.pi / 5) * (radius if k % 2 == 0 else radius * .44),
             cy - math.cos(k * math.pi / 5) * (radius if k % 2 == 0 else radius * .44))
            for k in range(10)]


def render_map(elapsed: float, scale: int = 1):
    """Return a 294 x 736 RGBA expanded map, scaled for the requested canvas."""
    s = scale
    ts = hud.START + max(0., min(STUDY['duration_s'], elapsed))
    distance = float(np.interp(ts, hud.tt, hud.dd))
    completed = sum(elapsed >= section['end_s'] for section in SECTORS)
    image = Image.new('RGBA', (294*s, 736*s))
    d = ImageDraw.Draw(image)

    def rect(box, fill):
        d.rectangle(tuple(round(v*s) for v in box), fill=fill)
    def text(x, y, value, size, fill=WHITE, anchor='lt', cjk=False, stroke=0):
        d.text((round(x*s), round(y*s)), str(value), font=font(size,s,cjk), fill=fill,
               anchor=anchor, stroke_width=round(stroke*s), stroke_fill=(0,0,0,255))

    # The source recording starts with this map already expanded.
    rect((0,0,294,29), WHITE)
    text(147,4,CONFIG['route_display_name'],18,(37,37,37,255),'mt')

    # Elevation and route occupy separate clipped surfaces, as in the recording.
    profile = Image.new('RGBA',(294*s,124*s),(16,21,22,100))
    pd = ImageDraw.Draw(profile)
    left = max(hud.ds, distance-450)
    right = min(hud.de, left+900)
    left = max(hud.ds, right-900)
    along = np.linspace(left,right,295)
    height = np.interp(along,hud.grid,hud.zs)
    low, high = float(np.min(height)-2), float(np.max(height)+16)
    pts = [(k*s, (122-(float(z)-low)/(high-low)*106)*s) for k,z in enumerate(height)]
    pd.polygon([(0,124*s)]+pts+[(294*s,124*s)],fill=(0,155,221,115))
    pd.line(pts,fill=BLUE,width=max(1,round(2*s)),joint='curve')
    rider_x = (distance-left)/(right-left)*294
    rider_y = 122-(float(np.interp(distance,hud.grid,hud.zs))-low)/(high-low)*106
    # Gate distance markers belong to the same known route profile.
    for section in SECTORS:
        along_gate = hud.ds+section['end_m']
        gx = (along_gate-left)/(right-left)*294
        if 5 < gx < 289:
            gy = 122-(float(np.interp(along_gate,hud.grid,hud.zs))-low)/(high-low)*106
            for yy in np.arange(gy+3,124,5):
                pd.line([(gx*s,yy*s),(gx*s,min(yy+2,124)*s)],fill=(255,255,255,100),width=max(1,s))
            pd.ellipse(((gx-6)*s,116*s,(gx+6)*s,128*s),fill=(12,12,12,255))
            pd.text((gx*s,120*s),str(section['sector']),font=font(7,s),fill=(255,20,0,255),anchor='mm')
    px, py = rider_x*s, (rider_y-10)*s
    pd.ellipse((px-5*s,py-5*s,px+5*s,py+5*s),fill=ORANGE,outline=WHITE,width=max(1,s))
    pd.polygon([(px-3*s,py+3*s),(px+3*s,py+3*s),(px,py+8*s)],fill=ORANGE)
    pd.ellipse((px-1.5*s,py-1.5*s,px+1.5*s,py+1.5*s),fill=WHITE)
    image.alpha_composite(profile,(0,29*s))
    grade = hud.stats(ts)['grade_estimated_percent']
    grade_color = (255,21,0,255) if grade>=9 else ((255,224,0,255) if grade>=4 else WHITE)
    text(269,149,f'{grade:.0f}',52,grade_color,'rb',stroke=1)
    text(291,145,'%',18,WHITE,'rb',stroke=1)

    field = Image.new('RGBA',(294*s,553*s),(11,15,17,110))
    md = ImageDraw.Draw(field)
    cx, cy = np.interp(ts,hud.tt,hud.x), np.interp(ts,hud.tt,hud.y)
    angle = float(np.interp(ts,hud.tt,hud.heading))
    dx,dy = hud.x-cx,hud.y-cy
    lateral = dx*math.cos(angle)-dy*math.sin(angle)
    forward = dx*math.sin(angle)+dy*math.cos(angle)
    zoom=.69
    xp = 147+lateral*zoom
    yp = 277-forward*zoom
    coords = np.column_stack((xp*s,yp*s))
    route = [tuple(q) for q in coords]
    def visible_lines(points, color, width):
        # Avoid drawing thousands of round joints outside the clipped map viewport.
        runs=[];run=[]
        for a,b in zip(points,points[1:]):
            visible=(max(a[0],b[0])>=-30*s and min(a[0],b[0])<324*s and
                     max(a[1],b[1])>=-30*s and min(a[1],b[1])<583*s)
            if visible:
                if not run:run.append(tuple(a))
                run.append(tuple(b))
            elif run:
                runs.append(run);run=[]
        if run:runs.append(run)
        for run in runs:md.line(run,fill=color,width=width,joint='curve')
    visible_lines(route,(0,0,0,255),14*s)
    visible_lines(route,(184,185,185,255),9*s)
    visible_lines(route,(214,214,214,255),5*s)
    past = coords[hud.tt < ts].tolist()+[(147*s,277*s)]
    if len(past)>1:
        visible_lines(past,(0,0,0,255),14*s)
        visible_lines(past,ORANGE,9*s)

    for section in SECTORS:
        gate_t = hud.START+section['end_s']
        gx = float(np.interp(gate_t,hud.tt,xp))
        gy = float(np.interp(gate_t,hud.tt,yp))
        if -20<gx<314 and -20<gy<573:
            if elapsed >= section['end_s']:
                md.ellipse(((gx-10)*s,(gy-10)*s,(gx+10)*s,(gy+10)*s),fill=(27,27,27,255))
                md.polygon([(a*s,b*s) for a,b in star_points(gx,gy,9)],fill=(255,186,21,255))
            else:
                md.ellipse(((gx-13)*s,(gy-13)*s,(gx+13)*s,(gy+13)*s),fill=(8,8,8,255))
                md.text((gx*s,(gy+.5)*s),str(section['sector']),font=font(17,s),fill=(255,25,8,255),anchor='mm')
    # GPS course relative to the eased camera; precise route position remains fixed.
    relative_angle = float(np.interp(ts,hud.tt,ACTUAL_HEADING))-angle
    arrow=[]
    for xx,yy in [(0,-13),(-8,10),(0,6),(8,10)]:
        arrow.append(((147+xx*math.cos(relative_angle)-yy*math.sin(relative_angle))*s,
                      (277+xx*math.sin(relative_angle)+yy*math.cos(relative_angle))*s))
    md.polygon(arrow,fill=ORANGE)
    md.line(arrow+[arrow[0]],fill=WHITE,width=2*s,joint='curve')
    image.alpha_composite(field,(0,153*s))

    rect((0,706,294,736),WHITE)
    d.ellipse((12*s,713*s,32*s,733*s),fill=(22,22,22,255))
    d.polygon([(a*s,b*s) for a,b in star_points(22,723,8)],fill=(247,177,14,255))
    text(39,711,f'{completed}/{len(SECTORS)}',18,(29,29,29,255))
    text(285,711,f'{(distance-hud.ds)/1000:.2f}/{STUDY["distance_m"]/1000:.2f}km',18,(29,29,29,255),'rt')
    return image
