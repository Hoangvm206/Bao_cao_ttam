"""Authorized dev-only marker demo. Never alters BE activation or invokes reboot."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
MARKER=Path('/usr/local/etc/otsa-update/rollback-proof-20261023.json')
TEST='otsa-rollback-demo-20261023'
ACTION=sys.argv[1]
assert os.geteuid()==0 and ACTION in ('baseline','prepare','mutate','test-boot','return-boot','cleanup','final')
def command(args):
 c=subprocess.run(args,capture_output=True,text=True,timeout=20)
 return {'rc':c.returncode,'stdout':c.stdout,'stderr':c.stderr}
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
mount=command(['mount','-p'])
root=next(line.split()[0] for line in mount['stdout'].splitlines() if line.split()[1]=='/')
out={'action':ACTION,'root_dataset':root,'test_id':TEST}
assert root in ('zroot/ROOT/default','zroot/ROOT/'+TEST)
assert not MARKER.is_symlink() and not MARKER.parent.is_symlink()
if ACTION in ('prepare','mutate','cleanup'):assert root=='zroot/ROOT/default'
if ACTION=='prepare':
 assert not MARKER.exists()
 free=os.statvfs('/');out['free_bytes']=free.f_bavail*free.f_frsize
 assert out['free_bytes']>2*1024**3,'Insufficient free space for lab demo'
 assert TEST not in command(['bectl','list','-H'])['stdout']
 with MARKER.open('x') as f:
  os.chmod(MARKER,0o600);json.dump({'test_id':TEST,'phase':'before'},f,sort_keys=True);f.flush();os.fsync(f.fileno())
if ACTION=='mutate':
 assert json.loads(MARKER.read_bytes())=={'test_id':TEST,'phase':'before'}
 with MARKER.open('w') as f:
  json.dump({'test_id':TEST,'phase':'after'},f,sort_keys=True);f.flush();os.fsync(f.fileno())
if MARKER.exists():
 payload=json.loads(MARKER.read_bytes());assert payload.get('test_id')==TEST
 out['marker']={'payload':payload,'sha256':digest(MARKER)}
 if ACTION=='test-boot':assert root=='zroot/ROOT/'+TEST and payload['phase']=='before'
 if ACTION in ('return-boot','cleanup'):assert root=='zroot/ROOT/default' and payload['phase']=='after'
elif ACTION in ('mutate','test-boot','return-boot','cleanup'):raise RuntimeError('Required marker missing')
if ACTION=='cleanup':MARKER.unlink();out['marker_removed']=True
out['be']=command(['bectl','list','-H'])
out['pool']=command(['zpool','status','-x'])
out['boot_time']=command(['sysctl','-n','kern.boottime'])
out['mounts']=mount
out['inventory']=command(['pkg','query','-a','%n|%v'])
out['inventory']['stdout']='\n'.join(s for s in out['inventory']['stdout'].splitlines() if s.startswith(('os-otsa-','os-wazuh-agent|','wazuh-agent|','opnsense|')))
paths=['/conf/config.xml','/tmp/rules.debug','/var/ossec/etc/ossec.conf','/var/ossec/etc/client.keys',
 '/usr/local/etc/otsa/package-update.json','/usr/local/etc/otsa/enrollment.json',
 '/usr/local/opnsense/mvc/app/views/OPNsense/Core/snapshot.volt',
 '/usr/local/opnsense/mvc/app/controllers/OPNsense/Core/Api/SnapshotsController.php',
 '/usr/local/opnsense/scripts/system/bectl.py','/usr/local/opnsense/service/conf/actions.d/actions_zfs.conf']
out['hashes']={p:digest(p) for p in paths if Path(p).is_file()}
pf=command(['pfctl','-sr']);out['pf_rules']={'rc':pf['rc'],'sha256':hashlib.sha256(pf['stdout'].encode()).hexdigest()}
cron=command(['crontab','-l']);out['root_crontab']={'rc':cron['rc'],'sha256':hashlib.sha256(cron['stdout'].encode()).hexdigest()}
out['marker_exists_after_action']=MARKER.exists()
print(json.dumps(out))
