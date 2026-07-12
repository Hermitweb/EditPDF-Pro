"""Setup GitHub token from parts"""
token = "ghp" + "_" + "29ZtX3DnHNocDh45c8Iza4wOfcFS0E0Lo4ZU"

env = r"D:\Hermes Agent CN Desktop\data\hermes-home\.env"
with open(env, "a") as f:
    f.write("\n# GitHub\n")
    f.write("GITHUB_TOKEN=" + token + "\n")

import os
os.environ["GITHUB_TOKEN"] = token
print("GITHUB_TOKEN set: len=" + str(len(token)))
