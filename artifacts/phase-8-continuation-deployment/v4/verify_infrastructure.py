import json,subprocess,sys
from datetime import UTC,datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,"E:/p8v4/source/artifacts/phase-8-runner-amendment/v4-complete")
from controls import write_new
BUCKET="fyp-p82-20261005-018da1d6-803656589923"
RUN="p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
def cli(name: str, args: list[str], region: str = "ap-southeast-2") -> dict:
    result = subprocess.run(["aws", *args, "--profile", "fyp-research", "--region", region,
                             "--no-cli-pager", "--output", "json"], capture_output=True, text=True, timeout=90)
    record = {"at_utc": datetime.now(UTC).isoformat(), "args": args, "region": region,
              "exit": result.returncode, "stderr": result.stderr, "result": json.loads(result.stdout) if result.returncode == 0 else result.stdout}
    write_new(HERE / (name + ".json"), record)
    if result.returncode:
        raise RuntimeError("AWS_READ_FAILED: " + name)
    return record["result"]


def price(name: str, service: str, filters: dict[str, str]) -> dict:
    return cli(name, ["pricing", "get-products", "--service-code", service, "--filters",
                     json.dumps([{"Type": "TERM_MATCH", "Field": k, "Value": v} for k, v in filters.items()])], "us-east-1")


def rates(value: dict) -> list[float]:
    return sorted({float(d["pricePerUnit"]["USD"]) for raw in value["PriceList"]
                   for offer in json.loads(raw)["terms"].get("OnDemand", {}).values()
                   for d in offer["priceDimensions"].values()})


data={
 'image':cli('image',['ec2','describe-images','--image-ids','ami-090b1140798d2d006']),
 'network':cli('network',['ec2','describe-security-groups','--group-ids','sg-076d87ac5db0a6f52']),
 'profile':cli('profile',['iam','get-instance-profile','--instance-profile-name','FYP-'+RUN]),
 'versioning':cli('versioning',['s3api','get-bucket-versioning','--bucket',BUCKET])}
assert data['image']['Images'][0]['State']=='available'
assert not data['network']['SecurityGroups'][0]['IpPermissions']
assert data['versioning']['Status']=='Enabled'
write_new(HERE/'infrastructure-verification.json',{'status':'PASS','no_inbound':True,'versioning':'Enabled','image_available':True,'profile_verified':True})
print('INFRASTRUCTURE_PASS')
