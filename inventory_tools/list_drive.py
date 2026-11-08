import subprocess, json, sys
CLI="/opt/hatch/bin/hatch_gws_cli"
def list_folder(fid):
    items=[]; token=None
    while True:
        params={"q":f"'{fid}' in parents and trashed=false","pageSize":100,"fields":"nextPageToken,files(id,name,mimeType,size,modifiedTime,parents)"}
        if token: params["pageToken"]=token
        out=subprocess.run([CLI,"drive","files","list","--params",json.dumps(params)],capture_output=True,text=True)
        if out.returncode!=0:
            print("ERR",fid,out.stdout,out.stderr,file=sys.stderr); break
        d=json.loads(out.stdout)
        # CLI may wrap?
        files=d.get("files",d.get("result",{}).get("files",[]))
        items.extend(files)
        token=d.get("nextPageToken") or d.get("result",{}).get("nextPageToken")
        if not token: break
    return items

def walk(fid,path,out):
    for it in list_folder(fid):
        p=f"{path}/{it['name']}"
        rec={"path":p,"id":it["id"],"name":it["name"],"mimeType":it.get("mimeType"),"size":int(it["size"]) if it.get("size") else None,"modifiedTime":it.get("modifiedTime")}
        out.append(rec)
        if it.get("mimeType")=="application/vnd.google-apps.folder":
            walk(it["id"],p,out)

root="1VwSp3NzWl-JVUkaxZ770V-upE0nDcS66"
out=[]
walk(root,"JW_October_2026",out)
with open("/home/hatch/workspace/jeremy_wu_redteam/inventory/drive_inventory.json","w") as f: json.dump(out,f,indent=2)
tot=sum(r["size"] or 0 for r in out if r["mimeType"]!="application/vnd.google-apps.folder")
print(f"items={len(out)} files={sum(1 for r in out if r['mimeType']!='application/vnd.google-apps.folder')} folders={sum(1 for r in out if r['mimeType']=='application/vnd.google-apps.folder')} total_bytes={tot}")
for r in out: print(r["size"], r["path"])
