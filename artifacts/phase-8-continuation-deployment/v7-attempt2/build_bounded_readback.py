from pathlib import Path

here=Path(__file__).resolve().parent
text=(here/'readback_and_stop.py').read_text(encoding='utf-8')
start="    target=Path('E:/p8v7/blocked-20261009-v7-attempt2')"
end="    actual={};manifest=None"
a=text.index(start);b=text.index(end,a)
replace='''    from concurrent.futures import ThreadPoolExecutor
    target=Path('E:/p8v7/blocked-20261009-v7-attempt2')
    partial=target/'evidence.tar.gz'
    assert partial.exists() and 0<partial.stat().st_size<proof['bytes']
    write_new(HERE/'blocked-evidence-timeout-retained.json',{'status':'FAILED_DOWNLOAD_TIMEOUT_RETAINED','timeout_seconds':180,'partial_file':str(partial),'partial_bytes':partial.stat().st_size,'partial_sha256':hash_file(partial),'same_pinned_version':proof['version_id'],'no_outcome_replayed':True})
    ranges=[]
    for offset in range(partial.stat().st_size,proof['bytes'],1048576):
        last=min(offset+1048576,proof['bytes'])-1
        ranges.append((offset,last,target/('readback-range-'+str(offset)+'.bin')))
    assert len(ranges)<=4
    def fetch(item):
        offset,last,path=item
        result=aws('blocked-range-'+str(offset),['s3api','get-object','--bucket',proof['bucket'],'--key',proof['key'],'--version-id',proof['version_id'],'--range','bytes='+str(offset)+'-'+str(last),str(path)],120)
        assert result['VersionId']==proof['version_id']
        assert result['ContentRange']=='bytes '+str(offset)+'-'+str(last)+'/'+str(proof['bytes'])
        assert path.stat().st_size==last-offset+1
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=[pool.submit(fetch,item) for item in ranges]
        for result in results:result.result()
    archive=target/'evidence-complete.tar.gz'
    with archive.open('xb') as output:
        output.write(partial.read_bytes())
        for _,_,path in ranges:output.write(path.read_bytes())
    assert archive.stat().st_size==proof['bytes'] and hash_file(archive)==proof['sha256']
'''
text=text[:a]+replace+text[b:]
with (here/'bounded_readback_and_stop.py').open('x',encoding='utf-8',newline='\n') as out:out.write(text)
