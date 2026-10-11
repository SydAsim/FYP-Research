from pathlib import Path

here=Path(__file__).resolve().parent
text=(here/'bounded_readback_and_stop.py').read_text(encoding='utf-8')
text=text.replace("    write_new(HERE/'blocked-preservation-proof.json',proof)","    assert read(HERE/'blocked-preservation-proof.json')==proof")
with (here/'bounded_readback_resume_and_stop.py').open('x',encoding='utf-8',newline='\n') as out:out.write(text)
