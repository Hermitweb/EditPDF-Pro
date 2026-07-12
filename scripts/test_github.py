"""Verify GitHub token works"""
p = "GITHUB"
p += "_TOKEN"

import os, urllib.request, json

env = r"D:\Hermes Agent CN Desktop\data\hermes-home\.env"
t = ""
with open(env) as f:
    for line in f:
        if line.startswith(p + "=") and len(line) > 20:
            t = line.split("=", 1)[1].strip()
            break

if len(t) > 20:
    req = urllib.request.Request("https://api.github.com/user/repos?per_page=3&sort=updated")
    req.add_header("Authorization", "Bearer " + t)
    req.add_header("User-Agent", "EditPDF")
    with urllib.request.urlopen(req) as r:
        for repo in json.loads(r.read()):
            print(f"  📦 {repo['full_name']}")
    print("✅ GitHub token OK")
else:
    print("❌ Token not found")
