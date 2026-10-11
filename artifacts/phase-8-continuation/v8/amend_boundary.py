"""Explicit version/boundary replacements in the separately copied runtime only."""
from prepare import SOURCE, PREFIX

root=SOURCE/PREFIX
path=root/'closed_restart.py'
text=path.read_text()
replacements={
    '82-original':'120-original', 'COUNT = 82':'COUNT = 120',
    '01a11705-11f1-792b-ae1e-36bfc6773842':'01a11705-11f1-75f4-b64e-8f0a3679518b',
    'cf6d4ff9e6e8916a8204c420076676fe9d9c746545ad686357b4e65a8f78710c':'3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46',
    'closed-82':'closed-120','CLOSED82':'CLOSED120','NEXT_SEQUENCE83':'NEXT_SEQUENCE121',
    'rows[COUNT]["arm"] != "B3"':'rows[COUNT]["arm"] != "P1"',
    '"PROTOCOL_STOP"':'"WALL_CLOCK_BACKWARD_STOP_ADMISSIONS"',
    'continuation-v7':'continuation-v8','"planned": 1418':'"planned": 1380',
    'record["planned"] != 1418':'record["planned"] != 1380',
    '"CLOSED_82_METADATA_IMPORT"':'"CLOSED_120_METADATA_IMPORT"',
}
for old,new in replacements.items():
    assert old in text,old
    text=text.replace(old,new)
path.write_text(text)
path=root/'reuse_prepare.py';text=path.read_text()
for old,new in {
    '/var/lib/p8-combined-v4/run':'/var/lib/p8-continuation-v7/run',
    'closed-82':'closed-120','"PROTOCOL_STOP"':'"WALL_CLOCK_BACKWARD_STOP_ADMISSIONS"',
    '"backed_up": 82':'"backed_up": 120','"planned": 1418':'"planned": 1380',
    'REUSED_HOST_CLOSED82_PREPARED':'REUSED_HOST_CLOSED120_PREPARED',
}.items():
    assert old in text,old
    text=text.replace(old,new)
path.write_text(text)
print('Only new boundary, provenance and retained-host metadata paths amended.')
