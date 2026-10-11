"""Reuse the reviewed cost model, adding the retained failed v5 preparation segment."""
from pathlib import Path

here = Path(__file__).resolve().parent
source = (here.parent / 'v5/preflight.py').read_text().replace('E:/p8v5/source', 'E:/p8v6/source')
source = source.replace('    ]\n    prior_compute', '''        (datetime.fromisoformat("2026-10-09T11:17:31.181234+00:00"), datetime.fromisoformat("2026-10-09T11:42:01.734251+00:00")),
    ]
    prior_compute''')
source = source.replace('v5 inventory subprocess overhead', 'v5 inventory subprocess and v6 complete metadata backup overhead')
(here / 'preflight.py').write_text(source)
