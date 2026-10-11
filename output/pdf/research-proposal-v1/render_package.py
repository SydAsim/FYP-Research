"""Render editable Mermaid diagrams and Markdown to reviewable PDFs."""
from pathlib import Path
import os, re, json, html, subprocess, sys
from urllib.parse import quote
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, CondPageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
NODE=Path('C:/Users/syeda/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
CLI=ROOT/'tmp/pdfs/mermaid-tools/node_modules/@mermaid-js/mermaid-cli/src/cli.js'
CHROME=Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
if not CHROME.exists(): CHROME=Path('C:/Program Files (x86)/Google/Chrome/Application/chrome.exe')
config=OUT/'mermaid-config.json'
config.write_text(json.dumps({'theme':'base','themeVariables':{'fontFamily':'Arial','fontSize':'19px','primaryColor':'#eef2ff','primaryBorderColor':'#5966b8','primaryTextColor':'#162339','lineColor':'#64748b','secondaryColor':'#e8f5ef','tertiaryColor':'#fff7e2'},'flowchart':{'htmlLabels':False,'curve':'linear','nodeSpacing':24,'rankSpacing':32},'sequence':{'useMaxWidth':False,'diagramMarginX':12,'actorMargin':36,'width':130,'messageMargin':30,'wrap':True}}),encoding='utf-8')
pp=OUT/'puppeteer-config.json'
pp.write_text(json.dumps({'executablePath':str(CHROME),'args':['--no-sandbox']}),encoding='utf-8')
if '--skip-diagrams' not in sys.argv:
    for mmd in sorted((OUT/'diagrams').glob('*.mmd')):
        for ext in ('svg','png'):
            target=mmd.with_suffix('.'+ext)
            if target.exists() and target.stat().st_mtime>=mmd.stat().st_mtime:
                continue
            result=subprocess.run([str(NODE),str(CLI),'-i',str(mmd),'-o',str(target),'-c',str(config),'-p',str(pp),'-b','white','-s','2','--size','1000'],capture_output=True,text=True,encoding='utf-8')
            if result.returncode: raise RuntimeError(result.stderr+result.stdout)
        print('Rendered',mmd.stem,flush=True)

FONTDIR=Path('C:/Windows/Fonts')
for name,file in [('Body','arial.ttf'),('BodyBold','arialbd.ttf'),('BodyItalic','ariali.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONTDIR/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Text',fontName='Body',fontSize=10.2,leading=14.5,spaceAfter=8,textColor=colors.HexColor('#253247')))
styles.add(ParagraphStyle(name='H1X',fontName='BodyBold',fontSize=26,leading=32,spaceAfter=16,textColor=colors.HexColor('#22357a')))
styles.add(ParagraphStyle(name='H2X',fontName='BodyBold',fontSize=17,leading=22,spaceBefore=12,spaceAfter=10,keepWithNext=True,textColor=colors.HexColor('#22357a')))
styles.add(ParagraphStyle(name='H3X',fontName='BodyBold',fontSize=12.5,leading=17,spaceBefore=10,spaceAfter=7,textColor=colors.HexColor('#33476e')))
styles.add(ParagraphStyle(name='Cell',fontName='Body',fontSize=8.8,leading=12.3,textColor=colors.HexColor('#253247')))
styles.add(ParagraphStyle(name='CellHead',parent=styles['Cell'],fontName='BodyBold',textColor=colors.white))
styles.add(ParagraphStyle(name='Caption',parent=styles['Text'],fontSize=9,leading=12.5,textColor=colors.HexColor('#546179')))

def inline(s):
    s=s.replace('—','-').replace('–','-').replace('−','-').replace('→',' -> ').replace('×',' x ').replace('±','+/-')
    links=[]
    def save(m):
        label,url=m.groups(); url=url.strip('<>')
        if not re.match(r'^https?://',url):
            if not Path(url).is_absolute(): url=str((OUT/url).resolve())
            url=Path(url).as_uri()
        token=f'LINKTOKEN{len(links)}END'
        links.append((token,f'<link href="{html.escape(url,quote=True)}" color="#334f9b">{html.escape(label)}</link>'))
        return token
    s=re.sub(r'\[([^\]]+)\]\((<[^>]+>|[^)]+)\)',save,s)
    s=html.escape(s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'`([^`]+)`',r'<font name="BodyBold">\1</font>',s)
    for token,value in links: s=s.replace(token,value)
    return s

WIDTH=A4[0]-92
class ProposalDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='H2X':
            title=flowable.getPlainText()
            if re.match(r'^\d+\.',title):
                key='section-'+title.split('.')[0]
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(title,key,0,False)
                self.notify('TOCEntry',(0,title,self.page,key))
def make_table(lines):
    rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in lines]
    rows=[r for r in rows if not all(re.match(r'^:?-+:?$',c) for c in r)]
    count=len(rows[0]); widths=None
    if count==2: widths=[WIDTH*.26,WIDTH*.74]
    elif count==3: widths=[WIDTH*.22,WIDTH*.28,WIDTH*.50]
    elif count==4: widths=[WIDTH*.20,WIDTH*.33,WIDTH*.28,WIDTH*.19]
    elif count==5: widths=[WIDTH*.18,WIDTH*.20,WIDTH*.28,WIDTH*.13,WIDTH*.21]
    elif count==6: widths=[WIDTH*.08]+[WIDTH*.184]*5
    elif count==7: widths=[WIDTH*.14,WIDTH*.10,WIDTH*.08,WIDTH*.08,WIDTH*.10,WIDTH*.29,WIDTH*.21]
    data=[[Paragraph(inline(c),styles['CellHead' if i==0 else 'Cell']) for c in r] for i,r in enumerate(rows)]
    t=Table(data,colWidths=widths or [WIDTH/count]*count,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#334779')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f1f4f9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#334779')),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#dce2eb'))]))
    return t

def footer(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#dde3ee'));canvas.line(46,39,A4[0]-46,39)
    canvas.setFont('Body',8);canvas.setFillColor(colors.HexColor('#64748b'))
    canvas.drawString(46,26,'Commit-Aware Voice Agent | Evidence review | Candidate, not frozen')
    canvas.drawRightString(A4[0]-46,26,str(doc.page))
    canvas.restoreState()

def render(md,pdf,onepage=False):
    lines=md.read_text(encoding='utf-8').splitlines();story=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1;continue
        if not onepage and line.startswith('## 1. '):
            story.append(PageBreak())
            story.append(Paragraph('Contents',styles['H2X']))
            toc=TableOfContents()
            toc.levelStyles=[ParagraphStyle('TOCText',parent=styles['Text'],fontSize=10.5,leading=19,spaceBefore=3)]
            story.extend([toc,PageBreak()])
        if re.match(r'^### (?:RQ\d|L\d+\.)',line):
            # Keep each question or literature comparison with its small table.
            block=[Paragraph(inline(line[4:]),styles['H3X'])];i+=1
            while i<len(lines) and not lines[i].strip().startswith('|'):
                if lines[i].strip():block.append(Paragraph(inline(lines[i].strip()),styles['Text']))
                i+=1
            table_lines=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i]);i+=1
            block.extend([make_table(table_lines),Spacer(1,10)])
            story.append(KeepTogether(block));continue
        if line.startswith('|'):
            block=[]
            while i<len(lines) and lines[i].strip().startswith('|'): block.append(lines[i]);i+=1
            t=make_table(block)
            if len(t._cellvalues)<=8 and len(t._cellvalues[0])==2:
                story.append(KeepTogether([t,Spacer(1,10)]))
            else:story.extend([t,Spacer(1,10)])
            continue
        if line.startswith('### Figure'):
            block=[Paragraph(inline(line[4:]),styles['H3X'])];i+=1
            while i<len(lines) and not lines[i].strip(): i+=1
            match=re.match(r'!\[.*?\]\((.*?)\)',lines[i].strip())
            if match:
                img=OUT/match.group(1);w,h=PILImage.open(img).size
                scale=min(WIDTH/w,500/h)
                block.extend([Image(str(img),width=w*scale,height=h*scale),Spacer(1,8)])
                i+=1
            for _ in range(2):
                while i<len(lines) and not lines[i].strip(): i+=1
                if i<len(lines): block.append(Paragraph(inline(lines[i]),styles['Caption']));i+=1
            story.extend([KeepTogether(block),Spacer(1,12)]);continue
        if line.startswith('# '):
            story.append(Paragraph(inline(line[2:]),styles['H1X']));i+=1;continue
        if line.startswith('## '):
            if not onepage and re.match(r'## (?:[2-9]|1[0-7])\.',line):story.append(PageBreak())
            story.append(Paragraph(inline(line[3:]),styles['H2X']));i+=1;continue
        if line.startswith('### '):story.extend([CondPageBreak(85),Paragraph(inline(line[4:]),styles['H3X'])]);i+=1;continue
        if re.match(r'^\d+\.\s',line):
            story.append(Paragraph(inline(line),styles['Text']));i+=1;continue
        if line.startswith('- '):
            story.append(Paragraph('&#8226; '+inline(line[2:]),styles['Text']));i+=1;continue
        block=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#','|','- ','![')) and not re.match(r'^\d+\.\s',lines[i].strip()):
            block.append(lines[i].strip());i+=1
        story.append(Paragraph(inline(' '.join(block)),styles['Text']))
    if onepage:
        # Adjust only this compact overview's local copy of body style.
        for f in story:
            if isinstance(f,Paragraph) and f.style.name=='Text': f.style=ParagraphStyle('OverviewBody',parent=styles['Text'],fontSize=10,leading=13.2,spaceAfter=8)
    doc=ProposalDoc(str(pdf),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=43,bottomMargin=52,title='Commit-Aware Voice Agent - '+('Plain-English Overview' if onepage else 'Research Proposal'),author='Syed Asim Bacha')
    doc.multiBuild(story,onFirstPage=footer,onLaterPages=footer)
    print('Created',pdf.name,flush=True)

render(OUT/'research-proposal.md',OUT/'research-proposal.pdf')
render(OUT/'plain-english-overview.md',OUT/'plain-english-overview.pdf',onepage=True)
