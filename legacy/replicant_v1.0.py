#!/usr/bin/env python3
"""
the_replicant.py — Harmless worm-behavior demo for training
- No network, no persistence, no privilege escalation.
- Copies itself into ./sandbox_w/replicas with a numeric suffix, up to LIMIT.
- Requires explicit --demo flag; default is inert.
- STOP file acts as a kill-switch (replication halted if present).
"""
import argparse
import shutil
import json
import time
import hashlib
import pathlib
# replicant (demo configuration)
w = {
	"sandbox": "sandbox_w",
	"replica_dir": "replicas",
	"limit": 3, # max number of harmless copies
	"marker": "STOP", # presence halts replication
}

def sha256(path):
	h = hashlib.sha256()
	with open(path, "rb") as f:
		for chunk in iter(lambda: f.read(8192), b""):
			h.update(chunk)
	return h.hexdigest()

def init_sandbox():
	"""
	Initializes the sandbox environment for safe replication.
	- Creates the replica directory and STOP kill-switch file.
	- Writes a manifest describing safety features and replication limit.
	"""
	base = pathlib.Path(w["sandbox"]) / w["replica_dir"]
	base.mkdir(parents=True, exist_ok=True)
	# Create STOP kill-switch
	stop = pathlib.Path(w["sandbox"]) / w["marker"]
	stop.write_text(
		f"This STOP file prevents replication. Remove it to allow up to {w['limit']} harmless copies.\n"
	)
	manifest = {
		"purpose": "Training-only harmless self-replication demo",
		"safety": {"network": False, "persistence": False, "privilege_escalation": False},
		"limit": w["limit"],
		"created": time.strftime("%Y-%m-%d %H:%M:%S"),
	}
	(pathlib.Path(w["sandbox"]) / "manifest.json").write_text(json.dumps(manifest, indent=2))
	print(f"[init] Sandbox ready at ./{w['sandbox']}. Remove STOP to allow a demo run.")

def replicate_once():
	"""
	Replicates the script into the sandbox's replica directory if the STOP file is absent and the replication limit is not exceeded.

	Checks for the STOP marker to ensure safety, counts existing replicas, and copies itself with a numeric suffix if allowed.
	"""
	base = pathlib.Path(w["sandbox"])
	if (base / w["marker"]).exists():
		print("[safe] STOP present; replication blocked.")
		return
	replicas = base / w["replica_dir"]
	replicas.mkdir(parents=True, exist_ok=True)
	existing = sorted(replicas.glob("wcopy*.py"))
	idx = len(existing) + 1
	if idx > w["limit"]:
		print("[done] Replication limit reached; no action taken.")
		return
	src = pathlib.Path(__file__).resolve()
	dst = replicas / f"wcopy{idx}.py"
	shutil.copy(src, dst)
	print(f"[replicate] {src.name} -> {dst}")
	print(f"[hash] src sha256={sha256(src)}")
	print(f"[hash] dst sha256={sha256(dst)}")

def main():
	"""
	Parses command-line arguments to control sandbox initialization and safe replication.
	- --init: Prepares sandbox and safety files.
	- --demo: Performs one safe replication if STOP file is removed.
	- Shows help if no arguments are provided.
	"""
	ap = argparse.ArgumentParser(description="Harmless worm-behavior demo (training only).")
	ap.add_argument("--init", action="store_true", help="Prepare sandbox and safety files.")
	ap.add_argument("--demo", action="store_true", help="Perform one safe replication (if STOP removed).")
	args = ap.parse_args()
	if args.init:
		init_sandbox()
		return
	if args.demo:
		replicate_once()
		return
	ap.print_help()

if __name__ == "__main__":
	main()