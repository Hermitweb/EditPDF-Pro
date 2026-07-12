import urllib.request, json, os, subprocess, sys
Z = os.environ.get("ZENTAO_URL","http://zd.iniess.cn/api.php/v1/")
U = os.environ.get("ZENTAO_USER","")
P = os.environ.get("ZENTAO_PASS","")
PRODUCT_ID = 3  # EditPDF Pro

_tok = ""
def _login():
    global _tok
    r = urllib.request.Request(Z.rstrip("/")+"/tokens",
        data=json.dumps({"account":U,"password":P}).encode(),
        headers={"Content-Type":"application/json","User-Agent":"EP"})
    _tok = json.loads(urllib.request.urlopen(r,timeout=10).read()).get("token","")

def api(path, data=None, method="GET"):
    if not _tok: _login()
    r = urllib.request.Request(Z.rstrip("/")+"/"+path, data=data,
        headers={"Token":_tok,"User-Agent":"EP"})
    r.method = method
    return json.loads(urllib.request.urlopen(r,timeout=10).read())

def my_tasks(): return api("tasks").get("tasks",[])
def create_bug(title, steps=""):
    return api("bugs",data=json.dumps({"product":PRODUCT_ID,"title":title,"steps":steps}).encode(),method="POST")
def create_task(name, desc=""):
    return api("tasks",data=json.dumps({"product":PRODUCT_ID,"name":name,"desc":desc}).encode(),method="POST")
def list_tasks():
    for t in my_tasks():
        s = t.get("status","")
        pid = t.get("product","")
        if str(pid)==str(PRODUCT_ID) and s in ("wait","doing"):
            print(f"  [{t.get(chr(105)+chr(100))}] {t.get(chr(110)+chr(97)+chr(109)+chr(101))} ({s})")

if __name__=="__main__":
    print(f"=== EditPDF Pro 待办 ===")
    list_tasks()
