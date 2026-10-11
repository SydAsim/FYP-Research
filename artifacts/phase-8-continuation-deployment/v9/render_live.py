"""External source and real dependency/backup gates, no main execution."""
from pathlib import Path
import json
from ops import HERE
from controls import read

def main():
    pkg=read(HERE/'deployment-manifest.json')['candidate'];freeze=read(HERE/'deployment-manifest.json')['freeze']
    prior=(HERE.parent/'v7-attempt3/render_live.py').read_text()
    prior=prior.replace('continuation-v7','continuation-v9').replace('9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817',pkg['package_hash']).replace('c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152',pkg['archive_sha256']).replace('3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46',freeze['freeze_manifest_sha256'])
    # This renders the already defined independent host_checks.py only.
    exec(compile(prior,'qualified_external_renderer','exec'),{'__file__':str(HERE/'render_live.py')})
    print('Live source/dependency/120-backup gate script prepared.')

if __name__=='__main__':main()
