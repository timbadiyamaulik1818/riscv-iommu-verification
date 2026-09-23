#!/usr/bin/env python3
"""Figures for both papers, drawn from ../results. Print-first: black line art,
series distinguished by style and label, one axis per chart."""
import os, re, json, math
from reportlab.pdfgen import canvas as C
from reportlab.lib.colors import black, white, Color

R='../results'; OUT='figures'
os.makedirs(OUT, exist_ok=True)
FILL=Color(.86,.86,.86); GREY=Color(.45,.45,.45); GRID=Color(.85,.85,.85)

def cv(n,w,h):
    c=C.Canvas(os.path.join(OUT,n),pagesize=(w,h)); c.setLineJoin(1); c.setLineCap(1); return c
def box(c,x,y,w,h,label,pt=6.6,lw=0.8,fill=None,dash=None):
    if fill: c.setFillColor(fill); c.rect(x,y,w,h,stroke=0,fill=1); c.setFillColor(black)
    c.setLineWidth(lw)
    if dash: c.setDash(*dash)
    c.rect(x,y,w,h,stroke=1,fill=0); c.setDash()
    c.setFont('Helvetica',pt); ls=label.split('\n'); n=len(ls)
    for i,l in enumerate(ls):
        c.drawCentredString(x+w/2, y+h/2+(n-1-2*i)*(pt+1)/2-pt/2+1.5, l)
def arr(c,x1,y1,x2,y2,lw=0.8,head=3.4,dash=None):
    c.setLineWidth(lw)
    if dash: c.setDash(*dash)
    c.line(x1,y1,x2,y2); c.setDash()
    a=math.atan2(y2-y1,x2-x1)
    for s in (1,-1):
        b=a+s*2.5; c.line(x2,y2,x2+head*math.cos(b),y2+head*math.sin(b))

# ---------------- A1: environment architecture ----------------
c=cv('figA1_env.pdf',516,210)
box(c,206,80,104,54,'RISC-V IOMMU\n(device under test)\n25,778 lines',pt=7,lw=1.4,fill=FILL)
box(c,20,140,150,26,'programming BFM\n(AXI4 -> registers)',pt=6.4)
box(c,20,88,150,26,'device request driver\n(AXI4 + stream_id)',pt=6.4)
box(c,20,36,150,26,'data-structure memory\n(DDT, page tables, CQ, FQ)',pt=6.4)
box(c,346,140,150,26,'completion checker\n(translated address)',pt=6.4)
box(c,346,88,150,26,'golden translation model\n(Sv39 / Sv39x4 walk)',pt=6.4)
box(c,346,36,150,26,'scoreboard (55 checks)',pt=6.4)
arr(c,170,153,206,125); arr(c,170,101,206,107); arr(c,206,95,170,62)
arr(c,310,120,346,153); arr(c,310,107,346,101)
arr(c,421,88,421,62); arr(c,421,140,421,114,dash=(2,2))
c.setFont('Helvetica-Oblique',6.2)
c.drawCentredString(258,20,'every arrow is an AXI4 channel pair; the golden model walks the same memory image')
c.save()

# ---------------- A2: mutation trajectory ----------------
stages=[('initial suite\n(34 checks)',4,9,'permission bits,\nreserved bits and\nsecond stage untested'),
        ('+ permission and\nreserved-bit tests\n(44 checks)',8,10,'invalid PTE and\nG-stage still untested'),
        ('+ invalid-PTE and\ntwo-stage tests\n(55 checks)',11,11,'all injected faults\ndetected')]
c=cv('figA2_mutation.pdf',516,190)
x0,y0,w,h=54,54,300,108
c.setStrokeColor(GRID); c.setLineWidth(0.4)
for v in (0,25,50,75,100):
    yy=y0+v/100*h; c.line(x0,yy,x0+w,yy)
c.setStrokeColor(black); c.setLineWidth(0.8); c.line(x0,y0,x0,y0+h); c.line(x0,y0,x0+w,y0)
c.setFont('Helvetica',6.2); c.setFillColor(GREY)
for v in (0,25,50,75,100): c.drawRightString(x0-3,y0+v/100*h-2,f'{v}%')
c.setFillColor(black)
bw=52
for i,(lab,d,t,note) in enumerate(stages):
    xx=x0+34+i*94; pct=100.0*d/t; bh=pct/100*h
    c.setFillColor(FILL); c.rect(xx,y0,bw,bh,stroke=0,fill=1); c.setFillColor(black)
    c.setLineWidth(1.0); c.rect(xx,y0,bw,bh,stroke=1,fill=0)
    c.setFont('Helvetica-Bold',7); c.drawCentredString(xx+bw/2,y0+bh+5,f'{d}/{t}')
    c.setFont('Helvetica',5.9)
    for j,l in enumerate(lab.split('\n')): c.drawCentredString(xx+bw/2,y0-10-j*7,l)
    c.setFont('Helvetica-Oblique',5.6); c.setFillColor(GREY)
    for j,l in enumerate(note.split('\n')): c.drawString(x0+w+12,y0+bh-4-j*7,l)
    c.setFillColor(black)
c.setFont('Helvetica',6.6)
c.saveState(); c.translate(x0-26,y0+h/2); c.rotate(90)
c.drawCentredString(0,0,'injected faults detected'); c.restoreState()
c.save()

# ---------------- A3: checks by category ----------------
out=open(os.path.join(R,'suite.txt')).read()
cats=[('register interface',['T1','T4']),('directory walk / modes',['T2','T3']),
      ('first-stage Sv39',['T5','T6','T10']),('second stage',['T14']),
      ('caching + invalidation',['T7','T8','T9','T15','T16']),
      ('faults + permissions',['T11','T12','T13'])]
counts=[]
for name,pfx in cats:
    n=sum(1 for l in out.splitlines() if l.strip().startswith(('PASS','FAIL'))
          and any(re.match(rf'\s*(PASS|FAIL)\s+{p}[a-z]?\b',l) for p in pfx))
    counts.append((name,n))
c=cv('figA3_checks.pdf',252,140)
gx,gw=124,108; mx=max(n for _,n in counts)
c.setLineWidth(0.8); c.line(gx,16,gx,130)
for i,(name,n) in enumerate(counts):
    yy=116-i*18; ln=max(n/mx*gw,1)
    c.setFillColor(FILL); c.rect(gx,yy,ln,12,stroke=0,fill=1); c.setFillColor(black)
    c.setLineWidth(0.7); c.rect(gx,yy,ln,12,stroke=1,fill=0)
    c.setFont('Helvetica',6.3); c.drawRightString(gx-4,yy+3.5,name)
    c.drawString(gx+ln+3,yy+3.5,str(n))
c.setFont('Helvetica',6.3); c.drawCentredString(gx+gw/2,6,'checks per functional area (55 total)')
c.save()

# ---------------- B1: ordering scenario ----------------
c=cv('figB1_ordering.pdf',516,142)
lx,rx=52,486; y=84
c.setLineWidth(0.9); c.line(lx,y,rx,y); arr(c,rx-12,y,rx,y)
ev=['device access\n(caches the\nmapping)','host rewrites\nthe page table','IOTINVAL.VMA',
    'IOFENCE.C','completion word\nvisible in memory','device access']
xs=[lx+30+i*((rx-lx-60)/5.0) for i in range(6)]
for xx,lab in zip(xs,ev):
    c.setLineWidth(0.8); c.line(xx,y-5,xx,y+5)
    c.setFont('Helvetica',6.2); ls=lab.split('\n')
    for j,l in enumerate(ls): c.drawCentredString(xx,y+14+(len(ls)-1-j)*7.6,l)
x4=xs[4]
c.setDash(2,2); c.setLineWidth(0.8); c.line(x4,y-58,x4,y+6); c.setDash()
c.setFont('Helvetica',6.3)
c.drawCentredString((lx+x4)/2,y-18,'stale mapping permitted')
c.drawCentredString((x4+rx)/2,y-18,'stale mapping is a violation')
box(c,lx,y-44,x4-lx,15,'IOTLB may still answer with the old translation',pt=6.2,dash=(2,2))
box(c,x4,y-44,rx-x4,15,'must answer with the new one',pt=6.2,fill=FILL)
c.setFont('Helvetica-Bold',6.6)
c.drawCentredString(258,y-56,'after the completion word is visible, no access may use the old mapping')
c.setFont('Helvetica-Oblique',6.0)
c.drawCentredString(258,10,'the same schedule is run with device traffic in flight throughout (24 concurrent accesses)')
c.save()

# ---------------- B2: concurrent-traffic ordering, baseline vs injected fault ----------------
c=cv('figB2_concurrent.pdf',516,190)
lx,rx=86,470
rows=[('unmodified RTL', 4, 20, 0, 'every post-fence access uses the new translation'),
      ('invalidate-all clears\nonly one IOTLB entry', 5, 19, 19, 'every post-fence access uses the stale translation')]
for r,(lab,pre,post,stale,note) in enumerate(rows):
    y=132-r*74
    c.setFont('Helvetica',6.6)
    for j,l in enumerate(lab.split('\n')): c.drawRightString(lx-10,y-2-j*8,l)
    n=pre+post; step=(rx-lx)/float(n)
    fx=lx+pre*step
    c.setLineWidth(0.8); c.line(lx,y,rx,y)
    for i in range(n):
        xx=lx+step*(i+0.5); post_f = i>=pre
        bad = post_f and i-pre < stale
        c.setLineWidth(0.7)
        if bad:
            c.setFillColor(black); c.circle(xx,y,2.6,stroke=1,fill=1); c.setFillColor(black)
        else:
            c.circle(xx,y,2.6,stroke=1,fill=0)
    c.setDash(2,2); c.setLineWidth(0.8); c.line(fx,y-18,fx,y+26); c.setDash()
    c.setFont('Helvetica-Bold',6.4); c.drawString(fx+4,y+20,'IOFENCE.C completion word visible')
    c.setFont('Helvetica-Oblique',6.2); c.drawString(fx+4,y-16,note)
    c.setFont('Helvetica',6.2); c.drawString(lx,y-16,'%d accesses before' % pre)
c.setFont('Helvetica',6.4)
c.circle(lx+4,26,2.6,stroke=1,fill=0); c.drawString(lx+12,24,'device access answered with the new translation')
c.setFillColor(black); c.circle(lx+250,26,2.6,stroke=1,fill=1)
c.drawString(lx+258,24,'answered with the stale translation (ordering violation)')
c.save()

print('figures:', ', '.join(sorted(os.listdir(OUT))))
print('checks per category:', counts)
