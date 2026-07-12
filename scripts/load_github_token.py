"""Load GITHUB_TOKEN from .env into current session"""
import os

env = r"D:\Hermes Agent CN Desktop\data\hermes-home\.env"
with open(env, "r") as f:
    for line in f:
        if "GITHUB_TOKEN=" in line:
            token = line.strip().split("=", 1)[1]
            if len(token) >= 30:
                os.environ["GITHUB_TOKEN"] = token
                print(f"Loaded: len={len(token)} ok={len(token)>30}")
                break
