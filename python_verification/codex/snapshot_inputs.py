from independent_pass1 import *
from datetime import datetime,timezone
rows=[]
for name,root in [('613',P1),('v7',P2)]:
 for rel in ['2_Data/2_Models/c_Climpact_indices','2_Data/2_Models','5_Figures']:
  files=[p for p in (root/rel).rglob('*') if p.is_file()];rows.append(dict(target=name,path=str(root/rel),files=len(files),bytes=sum(p.stat().st_size for p in files),time_utc=datetime.now(timezone.utc).isoformat()))
(OUT/'mirror_snapshot_final.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
