import urllib.request, json
d = json.dumps({"account":"200625","password":"Qin200625"}).encode()
r = urllib.request.Request("http://zd.iniess.cn/api.php/v1/tokens", data=d, headers={"Content-Type":"application/json"})
tok = json.loads(urllib.request.urlopen(r, timeout=10).read()).get("token", "")
print("Token:", tok[:8])

# Try to start project via PUT with status
body = json.dumps({"status": "doing", "begin": "2026-07-10", "realBegan": "2026-07-10"}).encode()
r2 = urllib.request.Request("http://zd.iniess.cn/api.php/v1/projects/3", data=body, headers={"Token": tok, "Content-Type": "application/json"})
r2.method = "PUT"
try:
    resp = json.loads(urllib.request.urlopen(r2, timeout=10).read())
    print("Status:", resp.get("status", resp)[:50])
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:100])

# Now try creating execution
body2 = json.dumps({"project": 3, "name": "Phase2-UI", "begin": "2026-07-10", "end": "2026-08-15"}).encode()
r3 = urllib.request.Request("http://zd.iniess.cn/api.php/v1/executions", data=body2, headers={"Token": tok, "Content-Type": "application/json"})
r3.method = "POST"
try:
    resp2 = json.loads(urllib.request.urlopen(r3, timeout=10).read())
    eid = resp2.get("id") if isinstance(resp2, dict) else resp2
    print(f"Execution OK: {resp2}")
except urllib.error.HTTPError as e:
    print("HTTP exec", e.code, e.read().decode()[:200])
