#!/usr/bin/env python3
"""
replicant_v1.1.py — Harmless worm-behavior demo for training (hardened)
- No network, no persistence, no privilege escalation.
- Copies itself into ./sandbox_w/replicas with a numeric suffix, up to
LIMIT.
- Requires explicit subcommands; default is inert.
- STOP file acts as a kill-switch (replication halted if present).
- Adds: logging, error handling, path validation, atomic copy,
cleanup, status.

Minimal runbook for demo:
1) python replicant_v1.1.py --init
2) Show status: python replicant_v1.1.py --status
3) Allow a demo run. Remove sandbox_w/STOP and replicate:
    rm sandbox_w/STOP
    python replicant_v1.1.py --demo
    python replicant_v1.1.py --status
4) Cleanup:
    python replicant_v1.1.py --cleanup
    python replicant_v1.1.py --status
"""

import argparse, json, logging, os, shutil, sys, tempfile, time
from pathlib import Path
import hashlib
# ----------------------- config -----------------------
w = {
"sandbox": "sandbox_w",
"replica_dir": "replicas",
"limit": 3, # max harmless copies
"marker": "STOP", # presence halts replication
"logfile": "w_demo.log",
}
# -------------------- /config -------------------------
# --- logging ---
logger = logging.getLogger("w_demo")
logger.setLevel(logging.INFO)
_h = logging.StreamHandler(sys.stdout)
_h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(_h)
def add_file_logger(sandbox: Path):
	try:
		logfile = sandbox / w["logfile"]
		fh = logging.FileHandler(logfile)
		fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
		logger.addHandler(fh)
		logger.info(f"Log file: {logfile}")
	except Exception as e:
		logger.warning(f"Could not attach file logger: {e}")
# --- utils ---
def sha256(path: Path) -> str:
	h = hashlib.sha256()
	with path.open("rb") as f:
		for chunk in iter(lambda: f.read(8192), b""):
			h.update(chunk)
	return h.hexdigest()

def is_within(child: Path, parent: Path) -> bool:
	try:
		child.resolve().relative_to(parent.resolve())
		return True
	except Exception:
		return False

def validate_config() -> None:
	if not isinstance(w.get("limit"), int) or w["limit"] < 0:
		raise ValueError("Config 'limit' must be a non-negative integer.")
	for key in ("sandbox", "replica_dir", "marker"):
		val = w.get(key)
		if not val or any(ch in str(val) for ch in "/\\"):
			raise ValueError(f"Config '{key}' must be a simple name without path separators.")

def sandbox_paths() -> tuple[Path, Path, Path]:
	sandbox = Path(w["sandbox"])
	replicas = sandbox / w["replica_dir"]
	marker = sandbox / w["marker"]
	return sandbox, replicas, marker

def atomic_copy(src: Path, dst: Path) -> None:
	"""Copy src to dst atomically (temp file + replace)."""
	dst_parent = dst.parent
	dst_parent.mkdir(parents=True, exist_ok=True)
	with tempfile.NamedTemporaryFile(dir=dst_parent, delete=False) as tf:
		tmp = Path(tf.name)
		with src.open("rb") as s, tmp.open("wb") as d:
			shutil.copyfileobj(s, d)
	os.replace(tmp, dst) # atomic on same filesystem

# --- commands ---
def cmd_init():
	sandbox, replicas, marker = sandbox_paths()
	sandbox.mkdir(parents=True, exist_ok=True)
	add_file_logger(sandbox)
	# STOP marker initialization (idempotent)
	try:
		if not marker.exists():
			marker.write_text(
				f"This STOP file prevents replication. "
				f"Remove it to allow up to {w['limit']} harmless copies.\n"
			)
		manifest = {
			"purpose": "Training-only harmless self-replication demo",
			"safety": {"network": False, "persistence": False, "privilege_escalation": False},
			"limit": w["limit"],
			"created": time.strftime("%Y-%m-%d %H:%M:%S"),
		}
		(sandbox / "manifest.json").write_text(json.dumps(manifest, indent=2))
		logger.info(f"Sandbox ready at ./{sandbox}. STOP present.")
	except (OSError, IOError) as e:
		logger.error(f"Init failed: {e}")
		sys.exit(1)

def cmd_demo():
	sandbox, replicas, marker = sandbox_paths()
	if not sandbox.exists():
		logger.error("Sandbox not initialized. Run: w_demo_v2.py --init")
		sys.exit(2)
	add_file_logger(sandbox)
	if marker.exists():
		logger.info("STOP present; replication blocked.")
		return
	replicas.mkdir(parents=True, exist_ok=True)
	# Determine next index
	existing = sorted(replicas.glob("w_copy_*.py"))
	idx = len(existing) + 1
	if idx > w["limit"]:
		logger.info("Replication limit reached; no action taken.")
		return
	src = Path(__file__).resolve()
	dst = (replicas / f"w_copy_{idx}.py").resolve()
	# Path safety: destination must be inside sandbox
	if not is_within(dst, sandbox):
		logger.error("Refusing to write outside sandbox.")
		sys.exit(3)
	try:
		atomic_copy(src, dst)
		logger.info(f"Replicated: {src.name} -> {dst}")
		logger.info(f"src sha256={sha256(src)}")
		logger.info(f"dst sha256={sha256(dst)}")
	except (OSError, IOError) as e:
		logger.error(f"Copy failed: {e}")
		sys.exit(4)

def cmd_status():
	sandbox, replicas, marker = sandbox_paths()
	if not sandbox.exists():
		print("Status: sandbox not initialized.")
		return
	add_file_logger(sandbox)
	copies = sorted(replicas.glob("w_copy_*.py")) if replicas.exists() else []
	print("=== STATUS ===")
	print(f"sandbox: {sandbox.resolve()}")
	print(f"STOP present: {marker.exists()}")
	print(f"limit: {w['limit']}")
	print(f"replicas: {len(copies)}")
	for c in copies:
		print(f" - {c.name} sha256={sha256(c)}")

def cmd_cleanup():
	sandbox, replicas, marker = sandbox_paths()
	if not sandbox.exists():
		print("Nothing to clean.")
		return
	add_file_logger(sandbox)
	# Recreate STOP, then remove replicas dir
	try:
		marker.write_text("STOP\n")
		if replicas.exists():
			shutil.rmtree(replicas)
		logger.info("Cleanup complete: replicas removed, STOP restored.")
	except (OSError, IOError) as e:
		logger.error(f"Cleanup failed: {e}")
		sys.exit(5)

def main():
	try:
		validate_config()
	except Exception as e:
		logger.error(f"Configuration error: {e}")
		sys.exit(10)
	ap = argparse.ArgumentParser(description="Harmless worm-behavior demo (training only).")
	ap.add_argument("--init", action="store_true", help="Prepare sandbox and safety files.")
	ap.add_argument("--demo", action="store_true", help="Perform one safe replication (if STOP removed).")
	ap.add_argument("--status", action="store_true", help="Show sandbox/replica status.")
	ap.add_argument("--cleanup", action="store_true", help="Remove replicas and restore STOP.")
	args = ap.parse_args()
	if args.init:
		cmd_init()
		return
	if args.demo:
		cmd_demo()
		return
	if args.status:
		cmd_status()
		return
	if args.cleanup:
		cmd_cleanup()
		return
	ap.print_help()

if __name__ == "__main__":
	main()