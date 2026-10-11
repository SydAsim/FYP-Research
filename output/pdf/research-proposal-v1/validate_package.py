"""Read-only project checks and documentation asset/link validation."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import csv, hashlib, json, re, xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse
from pypdf import PdfReader
import pdfplumber

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
results={"checked_at":datetime.now(timezone.utc).isoformat(),"documentation_only":True}
for label,name in [('historical','historical-hashes-before.json'),('final_candidate_source','candidate-source-final-hashes.json')]:
    inventory=json.loads((ROOT/'artifacts/phase-8-study-design/v4'/name).read_text(encoding='utf-8'))
    changed=[p for p,h in inventory.items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
    results[label+'_files']=len(inventory)
    results[label+'_changed']=changed
    assert not changed,(label,changed)
slots=json.loads((ROOT/'artifacts/phase-8-study-design/v4/main-slots.json').read_text(encoding='utf-8'))
review=json.loads((ROOT/'artifacts/phase-8-study-design/v4/review-decisions.json').read_text(encoding='utf-8'))
assert len(slots)==1500 and all(s['status']=='NOT_STARTED' and s['execution_id'] is None for s in slots)
assert review['review_receipt'] is None and review['freeze_hash'] is None
results.update(main_slots=len(slots),main_statuses=dict(Counter(s['status'] for s in slots)),main_execution_ids_present=0,review_receipt=None,freeze_hash=None)
(OUT/'documentation-preservation-check.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')

text=(OUT/'research-proposal.md').read_text(encoding='utf-8')
contract=(ROOT/'docs/04_TEST_EVALUATION_AND_TRACEABILITY.md').read_text(encoding='utf-8')
questions=re.findall(r'^- \*\*(RQ[1-9]):\*\* (.+)$',contract,re.M)
assert len(questions)==6
for rq,question in questions:assert question in text,(rq,question)
assert review['allocation']=={'CLEAN':300,'HIDDEN_COMMIT':100,'PLAYOUT':60,'OTHER_BOUNDARY':40}
inputs=json.loads((ROOT/'research/fixtures/phase8_design_v4/inputs.json').read_text(encoding='utf-8'))['main_inputs']
assert len(inputs)==500
cal=json.loads((ROOT/'artifacts/phase-8-study-design/v4/calibration-qualification.json').read_text(encoding='utf-8'))
assert len(cal['all_attempts'])==178 and cal['driver_status_counts']=={'COMPLETED':139,'FAILED':39}
qualified={(r['case_id'],r['arm']) for r in cal['all_attempts'] if r['qualification']['status']=='QUALIFIED_BOUNDARY'}
assert len(qualified)==150
rows=list(csv.DictReader((ROOT/'artifacts/research-remedies/v2/exploratory-outcomes.csv').open(encoding='utf-8-sig')))
assert len(rows)==18
business={arm:sum(r['final_business_state_correct']=='True' for r in rows if r['arm']==arm) for arm in ('B3','P1','P2')}
assert business=={'B3':5,'P1':5,'P2':5}
power=json.loads((ROOT/'artifacts/phase-8-study-design/v4/analysis-design.json').read_text(encoding='utf-8'))
for q,delta in ((.03,0),(.05,0),(.05,-.01),(.1,0)):
    row=next(r for r in power['power']['grid'] if r['discordance']==q and r['true_difference']==delta)
    assert f"{row['exact_power']*100:.2f}%" in text
results['selected_factual_checks']={'exact_contract_questions':[q for q,_ in questions],'main_inputs':len(inputs),'allocation':review['allocation'],'planned_slots':len(slots),'calibration_attempts':len(cal['all_attempts']),'qualified_case_arm_boundaries':len(qualified),'calibration_driver_status_counts':cal['driver_status_counts'],'revised_exploratory_executions':len(rows),'business_success_out_of_six':business,'power_grid_matches_source':True}
md_links=[]
for md in OUT.glob('*.md'):
    for target in re.findall(r'\]\((<[^>]+>|[^)]+)\)',md.read_text(encoding='utf-8')):
        target=target.strip('<>')
        if not target.startswith(('http://','https://','#')):
            path=Path(target)
            if not path.is_absolute():path=OUT/path
            md_links.append(path)
            assert path.exists(),(md.name,str(path))
referenced=[OUT/p for p in re.findall(r'!\[.*?\]\((diagrams/[^)]+\.png)\)',text)]
assert len(referenced)==len(set(referenced))
diagram_sizes={}
for png in referenced:
    for ext in ('mmd','svg','png'):assert png.with_suffix('.'+ext).exists()
    svg=ET.parse(png.with_suffix('.svg')).getroot()
    _,_,w,h=map(float,svg.attrib['viewBox'].split())
    scale=min((595.275590551-92)/w,500/h)
    diagram_sizes[png.stem]={'svg_width':w,'svg_height':h,'nominal_pdf_font_pt':round(19*scale,2)}
    assert 19*scale>=8.7,(png.name,19*scale)
results['diagram_count']=len(referenced)
results['diagram_legibility_geometry']=diagram_sizes
results['existing_local_markdown_links']=len(md_links)
pdf_results={}
for name in ('research-proposal','plain-english-overview'):
    pdf=OUT/(name+'.pdf'); reader=PdfReader(pdf)
    uris=[]
    for page in reader.pages:
        for annotation in page.get('/Annots',[]):
            a=annotation.get_object().get('/A',{})
            if '/URI' in a:uris.append(str(a['/URI']))
    for uri in uris:
        if uri.startswith('file:'):
            p=unquote(urlparse(uri).path)
            if re.match(r'^/[A-Za-z]:/',p):p=p[1:]
            assert Path(p).exists(),uri
    if name=='plain-english-overview':assert len(reader.pages)==1
    else:assert len(reader.outline)==17
    bounds=[]
    with pdfplumber.open(pdf) as doc:
        for i,page in enumerate(doc.pages,1):
            for c in page.chars:
                if c['x0']<43 or c['x1']>page.width-43 or c['top']<35 or c['bottom']>page.height-20:
                    bounds.append({'page':i,'text':c['text'],'bounds':[c['x0'],c['x1'],c['top'],c['bottom']]})
    assert not bounds,(name,bounds[:10])
    pdf_results[name]={'pages':len(reader.pages),'external_or_local_uri_links':len(uris),'outline_sections':len(reader.outline),'text_outside_bounds':bounds,'sha256':sha(pdf)}
results['pdf_checks']=pdf_results
results['documented_claim_status']='Limited local mechanisms demonstrated; comparative benefit and novelty unproven'
results['main_campaign_started']=False
(OUT/'quality-check.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pdf_checks':pdf_results,'diagrams':len(referenced),'historic_files_unchanged':results['historical_files'],'candidate_sources_unchanged':results['final_candidate_source_files'],'main_campaign_started':False},indent=2))
