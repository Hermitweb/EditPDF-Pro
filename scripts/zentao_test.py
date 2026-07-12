import urllib.request, json
b = "http://zd.iniess.cn/api.php/v1/"
lr = json.loads(urllib.request.urlopen(urllib.request.Request(b+"tokens",
    data=json.dumps({"account":"200625","password":"Qin200625"}).encode(),
    headers={"Content-Type":"application/json","User-Agent":"EP"})).read())
tok = lr.get("token","")
def q(p):
    r = urllib.request.Request(b+p,headers={"Token":tok,"User-Agent":"EP"})
    return json.loads(urllib.request.urlopen(r,timeout=10).read())
print("=== Products ===")
for x in q("products").get("products",[]): print("  " + str(x["id"]) + " " + x["name"])
print("=== Projects ===")
for x in q("projects").get("projects",[]): print("  " + str(x["id"]) + " " + x["name"] + " " + x.get("status",""))
print("=== My Tasks ===")
for x in q("tasks").get("tasks",[]):
    if x.get("status") in ("wait","doing"): print("  " + str(x["id"]) + " " + x["name"])
