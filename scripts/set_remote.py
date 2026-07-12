"""Set up git remote properly"""
import subprocess

with open(r"D:\Hermes Agent CN Desktop\data\hermes-home\.env") as f:
    for line in f:
        if line.startswith("GITHUB_") and len(line) > 20:
            t = line.split("=", 1)[1].strip()
            break

url = "https://Hermitweb:" + t + "@github.com/Hermitweb/EditPDF-Pro.git"

subprocess.run(["git", "remote", "remove", "origin"], cwd=r"D:\EditPDFPro", capture_output=True)
subprocess.run(["git", "remote", "add", "origin", url], cwd=r"D:\EditPDFPro", capture_output=True, text=True)
r = subprocess.run(["git", "remote", "-v"], cwd=r"D:\EditPDFPro", capture_output=True, text=True)
print(r.stdout.strip())
