set -euo pipefail
python3 - <<'MEASURE'
import json,shutil
from pathlib import Path
root=Path('/var/lib/p8-continuation-v9/run');p=json.loads((root/'prelaunch-backup-proof.json').read_text());arc=Path(p['archive']);folder=arc.with_suffix('').with_suffix('');readback=Path(p['readback_record']).parent
size=lambda d:sum(q.stat().st_size for q in d.rglob('*') if q.is_file())
print(json.dumps({'filesystem_free_bytes':shutil.disk_usage('/').free,'filesystem_total_bytes':shutil.disk_usage('/').total,'prelaunch_raw_metadata_bytes':size(folder),'prelaunch_readback_tree_bytes':size(readback),'prelaunch_archive_bytes':arc.stat().st_size,'complete_stage_write_bound_bytes':size(folder)+size(readback)+arc.stat().st_size+16*1024**2,'required_free_bytes':145670462448,'minimum_final_margin_bytes':1073741824,'historical_pause_unchanged':(root/'pause.json').exists()}))
MEASURE
