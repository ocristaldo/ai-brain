#!/usr/bin/env python3
import os, hashlib, sys, glob, yaml

CONFIG = yaml.safe_load(open("config.yaml","r"))
BACKUPS_DIR = CONFIG["paths"]["backups_dir"]

def sha256sum(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    files = sorted(glob.glob(os.path.join(BACKUPS_DIR, "brain-*.tgz")))
    if not files:
        print("No backups found")
        sys.exit(1)
    last = files[-1]
    digest = sha256sum(last)
    with open(last+".sha256","r") as f:
        recorded = f.read().split()[0]
    ok = (digest == recorded)
    print(f"Verify {os.path.basename(last)}: {'OK' if ok else 'FAIL'}")
    sys.exit(0 if ok else 2)

if __name__ == "__main__":
    main()
