import json, os, subprocess, sys, concurrent.futures, time
CLI="/opt/hatch/bin/hatch_gws_cli"
BASE="/home/hatch/workspace/jeremy_wu_redteam/drive_mirror"
inv=json.load(open("/home/hatch/workspace/jeremy_wu_redteam/inventory/drive_inventory.json"))
files=[r for r in inv if r["mimeType"]!="application/vnd.google-apps.folder"]
# skip the unzipped PCIC subtree: verified on Drive by size in prior pass and held locally in jeremy_pcic final
files=[r for r in files if "CanDCS-U6_PCIC_download_2026-10-19_unzipped" not in r["path"]]
mode=sys.argv[1] if len(sys.argv)>1 else "all"
def prio(r):
    p=r["path"]
    if "/1_Thesis/" in p or "/3_Code/" in p or "/4_Results/" in p or p.endswith("README.md"): return 0
    if "/2_Data/1_Observations/" in p or "/2_Data/3_Annual_index_tables/" in p or "/2_Data/4_Monthly_analysis/" in p: return 1
    if "/b_Daily_series/" in p: return 2
    if "/c_Climpact_indices/" in p: return 3
    if "/5_Figures/" in p: return 4
    return 5
files.sort(key=lambda r:(prio(r), r["path"]))
if mode=="priority0": files=[r for r in files if prio(r)==0]
log=open(f"/home/hatch/workspace/jeremy_wu_redteam/inventory/download_{mode}.log","a")
def dl(r):
    dest=os.path.join(BASE, r["path"])
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and r["size"] is not None and os.path.getsize(dest)==r["size"]:
        return (r["path"], "skip-ok")
    for attempt in range(3):
        out=subprocess.run([CLI,"drive","files","get","--params",json.dumps({"fileId":r["id"],"alt":"media"}),"--output",dest],capture_output=True,text=True)
        if os.path.exists(dest) and (r["size"] is None or os.path.getsize(dest)==r["size"]):
            return (r["path"], "ok")
        time.sleep(2*(attempt+1))
    got=os.path.getsize(dest) if os.path.exists(dest) else -1
    return (r["path"], f"FAIL want={r['size']} got={got}")
done=0
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    for path,status in ex.map(dl, files):
        done+=1
        log.write(f"{status}\t{path}\n"); log.flush()
        if done%200==0: print(f"{done}/{len(files)}", flush=True)
print("DONE", len(files))
