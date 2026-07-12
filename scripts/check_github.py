"""Verify GitHub API token from .env"""
import os, urllib.request, json

env = r"D:\Hermes Agent CN Desktop\data\hermes-home\.env"
token = ""
with open(env, "r") as f:
    for line in f:
        if line.startswith("GITHUB_TOKEN=") and "ghp" in line:
            token = line.strip().split("=", 1)[1]
            break

if not token:
    print("No token found in .env, checking env var")
    token = os.environ.get("GITHUB_TOKEN", "")

print(f"Token found: len={len(token)}, first={token[:6]}...")

if len(token) > 20:
    req = urllib.request.Request("https://api.github.com/user")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("User-Agent", "Hermes")
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read())
        print("✅ GitHub: " + d.get("login", "?") + " (" + d.get("name", "") + ")")
