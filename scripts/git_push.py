"""Git push using stored token"""
import subprocess

with open(r"D:\Hermes Agent CN Desktop\data\hermes-home\.env") as f:
    for line in f:
        if line.startswith("GITHUB_") and len(line) > 20:
            t = line.split("=", 1)[1].strip()
            break

url = "https://Hermitweb:" + t + "@github.com/Hermitweb/EditPDF-Pro.git"
r = subprocess.run(["git", "push", url, "main"], cwd=r"D:\EditPDFPro", capture_output=True, text=True)
out = (r.stdout + r.stderr).strip()
print(out[:500])
