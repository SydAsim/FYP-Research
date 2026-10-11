from pathlib import Path

here = Path(__file__).resolve().parent
text = (here.parent / 'v7/prestart.py').read_text(encoding='utf-8')
text = text.replace("NAME='retained-host-v7-preparation-stop-20261009'", "NAME='retained-host-v7-attempt2-preparation-stop-20261009'")
text = text.replace("    repo=HERE.parents[2]", "    selection=read(HERE/'wrapper-selection-check.json')\n    assert selection['status']=='PASS_BEFORE_BOOT_COMMAND_SELECTION'\n    assert hash_file(HERE/'prepare-source-attempt2.sh')==selection['wrapper_sha256']\n    repo=HERE.parents[2]")
marker = '    # Original clock and signed cost model remain active even during preparation.'
insert = '''    # Replacement is verified before disabling only exact owned, obsolete preparation guards.
    schedules=aws('preparation-schedules-inventory',['scheduler','list-schedules','--group-name',GROUP])
    obsolete=[]
    known={'retained-host-preparation-stop','retained-host-v7-preparation-stop-20261009'}
    for entry in schedules.get('Schedules',[]):
        if entry['Name']==NAME:
            continue
        detail=aws('old-guard-'+entry['Name']+'-read',['scheduler','get-schedule','--name',entry['Name'],'--group-name',GROUP])
        if entry['Name'] not in known:
            if detail['State']=='ENABLED' and detail['Target'].get('RoleArn')==role['Arn'] and json.loads(detail['Target'].get('Input','{}')).get('InstanceIds')==[INSTANCE]:
                raise ValueError('UNREVIEWED_OWNED_PREPARATION_SCHEDULE')
            continue
        assert detail['Target']['Arn']==target['Arn'] and detail['Target']['RoleArn']==role['Arn']
        assert json.loads(detail['Target']['Input'])=={'InstanceIds':[INSTANCE]}
        if detail['State']=='ENABLED':
            payload={k:detail[k] for k in ('Name','GroupName','ScheduleExpression','ScheduleExpressionTimezone','FlexibleTimeWindow','Target')}
            for optional in ('Description','StartDate','EndDate','KmsKeyArn','ActionAfterCompletion'):
                if optional in detail:
                    payload[optional]=detail[optional]
            payload['State']='DISABLED'
            payload_path=HERE/(entry['Name']+'-disable.json')
            write_new(payload_path,payload)
            aws('old-guard-'+entry['Name']+'-disable',['scheduler','update-schedule','--cli-input-json','file://'+str(payload_path)])
            disabled=aws('old-guard-'+entry['Name']+'-readback',['scheduler','get-schedule','--name',entry['Name'],'--group-name',GROUP])
            assert disabled['State']=='DISABLED' and disabled['Target']==detail['Target']
        obsolete.append({'name':entry['Name'],'prior_state':detail['State'],'new_state':'DISABLED'})
    replacement=aws('preparation-replacement-final-read',['scheduler','get-schedule','--name',NAME,'--group-name',GROUP])
    assert replacement['State']=='ENABLED' and replacement['Target']==target
    write_new(HERE/'superseded-preparation-guards.json',{'status':'PASS','replacement_verified_before_changes':True,'obsolete':obsolete,'hard_deadline_guards_modified':False})
'''
assert marker in text
text = text.replace(marker, insert + marker)
with (here / 'prestart.py').open('x',encoding='utf-8',newline='\n') as f:
    f.write(text)
