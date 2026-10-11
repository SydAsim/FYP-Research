"""Retain a failed bounded first attempt without replacing its outcome."""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
path = here / 'attempt1/qualification.json'
assert not path.exists()
path.write_text(json.dumps({
    'status': 'FAIL_TIMEOUT_RETAINED', 'test_timeout_seconds': 300,
    'driver_exit': 124, 'completed_checks': 1, 'interrupted_check': 'test_complete_master_roundtrip',
    'run_log': 'run.json', 'first_roundtrip_succeeded': True,
    'secondary_preservation_copy_timeout_seconds': 30,
    'local_control_stop_request_timeout_seconds': 15,
    'original_test_container_retained': 'p85-v6-metadata-attempt1',
    'partial_local_copy_retained': 'failed-metadata',
    'AWS_started': False, 'research_executions': 0,
}, indent=2))
