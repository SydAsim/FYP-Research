import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const out = path.dirname(fileURLToPath(import.meta.url));
const base = path.resolve('artifacts/phase-8-operations/driver-diagnosis-145-v1');
const summaryPath = path.join(base, 'bounded-review/provisional-summary.json');
const inspection = 'E:/p8driver145v1/provisional2/inspection';
const ledgerPath = path.join(inspection, 'read-only-ledger.json');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const summaryBytes = await fs.readFile(summaryPath);
const ledgerBytes = await fs.readFile(ledgerPath);
const summary = JSON.parse(summaryBytes);
const manifest = JSON.parse(await fs.readFile(path.join(inspection, 'manifest.json'), 'utf8'));
if (hash(ledgerBytes) !== manifest.files['read-only-ledger.json']) throw Error('Retained ledger hash mismatch');
const ledger = JSON.parse(ledgerBytes).rows;
const slots = ledger.filter(r => r.state === 'BACKED_UP');
if (ledger.length !== 1500 || slots.length !== 145 || ledger.filter(r => r.state === 'PLANNED').length !== 1355) throw Error('Unexpected retained boundary');
const saved = new Map(summary.locally_full_archive_verified_outcomes.map(r => [r.sequence, r]));
if (saved.size !== 39 || summary.unavailable_outcome_slots.length !== 106) throw Error('Unexpected saved-grade availability');
const endpoints = Object.keys(summary.locally_full_archive_verified_outcomes[0].values);
const fields = ['sequence','case_id','arm','attempt','retained_state','result_availability','raw_status',
  ...endpoints,'failure_type','original_censor_reason','voice_evidence','execution_id','observation_deadline_utc',
  'fixture_sha256','backup_receipt_sha256','archive_sha256','export_sha256','pinned_archive_version'];
const missing = 'UNAVAILABLE_LOCALLY';
const rows = slots.map((r, i) => {
  if (r.sequence !== i+1 || r.attempt !== 1) throw Error('Saved order/attempt mismatch');
  const s = saved.get(r.sequence);
  if (s && (s.execution_id !== r.execution_id || s.arm !== r.arm || s.case_id !== r.case_id)) throw Error('Saved grade identity mismatch');
  return [r.sequence,r.case_id,r.arm,r.attempt,r.state,s ? 'VERIFIED_SAVED_GRADE' : missing,s?.raw_status ?? missing,
    ...endpoints.map(k => s ? s.values[k] : missing),s ? (s.failure_type ?? '') : missing,
    s ? (s.original_censor_reason ?? '') : missing,s?.voice_evidence ?? missing,r.execution_id,r.deadline,
    r.fixture_hash,r.backup_hash,s?.archive_sha256 ?? missing,s?.export_sha256 ?? missing,s?.version_id ?? missing];
});
if (rows.filter(r => r[5] === 'VERIFIED_SAVED_GRADE').length !== 39) throw Error('Lost saved grade');
await fs.mkdir(out, {recursive:true});
const wb = Workbook.create();
const results = wb.worksheets.add('Results');
const notes = wb.worksheets.add('Read me');
results.getRange('A1').write([fields, ...rows]);
const full = results.getRangeByIndexes(0,0,rows.length+1,fields.length);
full.format.font = {name:'Arial',size:10};
full.format.verticalAlignment = 'center';
full.format.columnWidth = 31;
full.format.rowHeight = 20;
const header = results.getRangeByIndexes(0,0,1,fields.length);
header.format = {fill:'#243B53',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:55};
results.getRange('A1:A146').format.columnWidth=10;
results.getRange('B1:B146').format.columnWidth=20;
results.getRange('C1:E146').format.columnWidth=15;
results.getRange('F1:F146').format.columnWidth=33;
results.getRangeByIndexes(0,fields.indexOf('execution_id'),146,1).format.columnWidth=47;
results.getRangeByIndexes(0,fields.indexOf('observation_deadline_utc'),146,1).format.columnWidth=43;
results.getRange('A2:A146').setNumberFormat('0');
results.getRange('D2:D146').setNumberFormat('0');
results.freezePanes.freezeRows(1);
results.showGridLines=false;
results.tables.add(`A1:${String.fromCharCode(64+Math.floor((fields.length-1)/26))}${String.fromCharCode(65+(fields.length-1)%26)}146`,true,'RetainedResults');
results.getRange('F2:F146').conditionalFormats.add('containsText',{text:missing,format:{fill:'#FFF3CD',font:{color:'#7A4D00'}}});
const instructions = [
  ['Phase 8 retained results','145 execution slots; 49 distinct inputs; 48 complete B3/P1/P2 sets. Study remains incomplete and paused.'],
  ['Available grades','39 verified saved grades. The other 106 outcomes have not been retrieved locally. No new grading or analysis was run.'],
  ['BACKED_UP','Evidence retention state. This does not mean the business or speech outcome passed.'],
  ['UNAVAILABLE_LOCALLY','The result is absent from this local export. It is not a research UNKNOWN, failure, success or silence finding.'],
  ['Raw failures','Original raw FAILED statuses and censor reasons are preserved. Accepted timing sidecars for the first originals remain separate in the bundle.'],
  ['Voice evidence','SCRIPTED_TONE_SEMANTIC_PROXY uses scripted tone/playback acknowledgements. It does not establish actual hearing or human understanding.'],
  ['Dates','Observation deadlines remain exact original UTC text, preserving microseconds. Dates were not rounded or converted.'],
  ['Source: saved-summary.json',hash(summaryBytes)],
  ['Source: retained-ledger-145.json',hash(ledgerBytes)+' (full original ledger hash; delivered ledger is the first-145 subset)'],
];
notes.getRange('A1').write(instructions);
notes.getRange('A1:B9').format.font={name:'Arial',size:11};
notes.getRange('A1:A9').format.font={name:'Arial',size:11,bold:true};
notes.getRange('A1:A9').format.columnWidth=32;
notes.getRange('B1:B9').format.columnWidth=120;
notes.getRange('A1:B9').format.wrapText=true;
notes.getRange('A1:B9').format.rowHeight=48;
notes.showGridLines=false;
wb.recalculate();
const rendered = await wb.render({sheetName:'Results',range:'A1:G8',scale:1,format:'png'});
await fs.writeFile(path.join(out,'results-preview.png'),new Uint8Array(await rendered.arrayBuffer()));
const readmePreview = await wb.render({sheetName:'Read me',range:'A1:B9',scale:1,format:'png'});
await fs.writeFile(path.join(out,'readme-preview.png'),new Uint8Array(await readmePreview.arrayBuffer()));
const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(path.join(out,'phase-8-retained-results-145.xlsx'));
const quote = value => '"'+String(value ?? '').replaceAll('"','""')+'"';
await fs.writeFile(path.join(out,'phase-8-retained-results-145.csv'),'\ufeff'+[fields,...results.getRangeByIndexes(1,0,145,fields.length).values].map(row=>row.map(quote).join(',')).join('\r\n')+'\r\n');
await fs.writeFile(path.join(out,'saved-summary.json'),summaryBytes);
await fs.writeFile(path.join(out,'retained-ledger-145.json'),JSON.stringify({source_sha256:hash(ledgerBytes),rows:slots},null,2));
const sidecars=[];
for (const source of summary.sidecars_preserved) {
  const b = await fs.readFile(source);
  const name=path.basename(source);
  await fs.mkdir(path.join(out,'timing-sidecars'),{recursive:true});
  await fs.writeFile(path.join(out,'timing-sidecars',name),b);
  sidecars.push({file:'timing-sidecars/'+name,sha256:hash(b)});
}
const checks={slots:145,verified_saved_grades:39,unavailable_locally:106,rows_in_saved_order:true,retained_ledger_member_hash_verified:true,
  no_regrading:true,no_network_or_aws_operations:true,sidecars,source_summary_sha256:hash(summaryBytes),source_ledger_sha256:hash(ledgerBytes)};
await fs.writeFile(path.join(out,'verification.json'),JSON.stringify(checks,null,2));
await fs.writeFile(path.join(out,'README.md'),'# Phase 8 retained results\n\n'+instructions.map(([a,b])=>`**${a}:** ${b}`).join('\n\n')+'\n\nThe XLSX and CSV contain all 145 retained execution identities. Original source files remain unchanged. This bundle does not contain the full execution archives.\n');
console.log(JSON.stringify(checks,null,2));
