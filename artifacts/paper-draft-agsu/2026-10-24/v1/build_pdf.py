"""Build a four-page review manuscript from editable Markdown; no research calls."""
from __future__ import annotations
import argparse,hashlib,json,re
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY,TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]

def inline(text: str) -> str:
    text=escape(text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    return re.sub(r'\*(.+?)\*',r'<i>\1</i>',text)

def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    for name,file in [('TNR','times.ttf'),('TNR-Bold','timesbd.ttf'),('TNR-Italic','timesi.ttf'),('TNR-BoldItalic','timesbi.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
    pdfmetrics.registerFontFamily('TNR',normal='TNR',bold='TNR-Bold',italic='TNR-Italic',boldItalic='TNR-BoldItalic')
    styles={
        'body':ParagraphStyle('body',fontName='TNR',fontSize=10.1,leading=12.8,spaceAfter=5,alignment=TA_JUSTIFY,splitLongWords=True),
        'title':ParagraphStyle('title',fontName='TNR-Bold',fontSize=19,leading=22,alignment=TA_CENTER,spaceAfter=11),
        'author':ParagraphStyle('author',fontName='TNR',fontSize=10,leading=12,alignment=TA_CENTER,spaceAfter=4),
        'note':ParagraphStyle('note',fontName='TNR-Italic',fontSize=8.3,leading=10.1,alignment=TA_CENTER,spaceAfter=10,textColor=colors.HexColor('#444444')),
        'heading':ParagraphStyle('heading',fontName='TNR-Bold',fontSize=11.1,leading=13.4,spaceBefore=7,spaceAfter=5,keepWithNext=True),
        'caption':ParagraphStyle('caption',fontName='TNR-Italic',fontSize=9,leading=11,spaceBefore=4,spaceAfter=5),
        'table':ParagraphStyle('table',fontName='TNR',fontSize=9.2,leading=11.1,alignment=TA_LEFT),
        'tablehead':ParagraphStyle('tablehead',fontName='TNR-Bold',fontSize=9.2,leading=11.1),
        'ref':ParagraphStyle('ref',fontName='TNR',fontSize=8.4,leading=10.4,spaceAfter=4,alignment=TA_LEFT),
    }
    text=(HERE/'paper.md').read_text(encoding='utf-8')
    assert len(text.split('<!-- PAGE_BREAK -->'))==4
    summary=json.loads((HERE/'pooled-outcomes.json').read_bytes())
    assert summary['completed_originals']==1318 and summary['pooled_values']['final_business_state_correct']['TRUE']==1198
    assert summary['pooled_values']['complete_corrective_communication']=={'NOT_APPLICABLE':1225,'TRUE':31,'FALSE':48,'UNKNOWN':14}
    assert not summary['verification_failures']
    doc=SimpleDocTemplate(str(args.output),pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,topMargin=18*mm,bottomMargin=18*mm,title='Commit-Aware Agents: Linking Transactional Evidence to Outcome Claims and Durable Correction',author='Syed Asim Bacha',subject='Work-in-progress scope-review draft; synthetic protocol evaluation; interim results',pageCompression=1)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    story=[];references=False
    for page_number,page in enumerate(text.split('<!-- PAGE_BREAK -->')):
        if page_number:story.append(PageBreak())
        blocks=re.split(r'\n\s*\n',page.strip())
        for block in blocks:
            block=block.strip()
            if not block:continue
            if block.startswith('# '):story.append(Paragraph(inline(block[2:]),styles['title']));continue
            if block.startswith('## '):
                references=block[3:]=='References'
                story.append(Paragraph(inline(block[3:]),styles['heading']));continue
            if block.startswith('|'):
                rows=[]
                for line in block.splitlines():
                    cells=[c.strip() for c in line.strip().strip('|').split('|')]
                    if all(re.fullmatch(r':?-+:?',x) for x in cells):continue
                    rows.append(cells)
                widths=[114,doc.width-114] if len(rows[0])==2 else [doc.width-194,44,47,61,42]
                content=[[Paragraph(inline(c),styles['tablehead'] if r==0 else styles['table']) for c in row] for r,row in enumerate(rows)]
                table=Table(content,colWidths=widths,hAlign='LEFT',repeatRows=1)
                table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('LINEABOVE',(0,0),(-1,0),.6,colors.black),('LINEBELOW',(0,0),(-1,0),.4,colors.black),('LINEBELOW',(0,-1),(-1,-1),.6,colors.black),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
                story.extend([table,Spacer(1,6)]);continue
            if page_number==0 and ('Department of Computer Science' in block or block=='**Syed Asim Bacha**' or block=='syedasimbacha5@gmail.com'):
                style=styles['author']
            elif block.startswith('*Work-in-progress'):style=styles['note']
            elif block.startswith('Table '):style=styles['caption']
            else:style=styles['ref'] if references else styles['body']
            story.append(Paragraph(inline(' '.join(block.splitlines())),style))
    def chrome(canvas,document):
        canvas.saveState();canvas.setFont('TNR',8);canvas.setFillColor(colors.HexColor('#555555'))
        if document.page>1:
            canvas.drawString(doc.leftMargin,A4[1]-11*mm,'S. A. Bacha / Commit-Aware Agents - work in progress')
        canvas.drawString(doc.leftMargin,11*mm,'Scope-review draft - 24 October 2026 - not submitted')
        canvas.drawRightString(A4[0]-doc.rightMargin,11*mm,f'{document.page} / 4')
        canvas.restoreState()
    doc.build(story,onFirstPage=chrome,onLaterPages=chrome)
    reader=PdfReader(args.output)
    result={'pdf':str(args.output.resolve()),'pages':len(reader.pages),'words':len(re.findall(r'\b\S+\b',text)),'per_page_characters':[len(p.extract_text() or '') for p in reader.pages],'pdf_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((HERE/'paper.md').read_bytes()).hexdigest()}
    print(json.dumps(result))
    if len(reader.pages)!=4:raise SystemExit('REVIEW_PDF_MUST_HAVE_EXACTLY_FOUR_PAGES')

if __name__=='__main__':main()
