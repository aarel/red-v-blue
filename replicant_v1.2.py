#!/usr/bin/env python3
"""
replicant_v1.2.py — Harmless worm-behavior demo (training only)
- SAFE: no network, no persistence, no privilege escalation.
- Demonstrates: local self-replication, optional simulated "spread", optional polymorphism, optional harmless payload.
- Safety rails: explicit flags, STOP kill-switch, hard replication LIMIT, path confinement to sandbox.

Optional extras:
  --polymorph        -> add a random, unused comment to each replica (checksum changes)
  --simulate-spread  -> also copy into mock 'hosts/host_*' dirs inside sandbox (no network)
  --payload          -> write a friendly note file alongside each replica

Commands:
  --init, --demo, --status, --cleanup

Minimal runbook 
1) Initialize sandbox (creates STOP file):
   python replicant_v1.2.py --init
   python replicant_v1.2.py --status
2) Enable a demo (remove the kill-switch) and replicate with optional extras
   rm sandbox_w/STOP
   python replicant_v1.2.py --demo --polymorph --simulate-spread --payload
   python replicant_v1.2.py --status
3) Cleanup (removes replicas, restores STOP):
   python replicant_v1.2.py --cleanup
   python replicant_v1.2.py --status
"""
   
from __future__ import annotations
import argparse, json, logging, os, random, shutil, sys, tempfile, time
from pathlib import Path
import hashlib
from typing import Tuple

try:
    # optional: nicer status if available
    from colorama import Fore, Style, init as _color_init
    _color_init()
    C_OK = Fore.GREEN
    C_WARN = Fore.YELLOW
    C_ERR = Fore.RED
    C_DIM = Style.DIM
    C_RST = Style.RESET_ALL
    COLORAMA_AVAILABLE = True
except Exception:
    C_OK = C_WARN = C_ERR = C_DIM = C_RST = ""
    COLORAMA_AVAILABLE = False

# ----------------------- config -----------------------
CFG = {
    "sandbox": "sandbox_w",
    "replica_dir": "replicas",
    "hosts_root": "hosts",     # for simulated spread
    "host_count": 3,           # number of mock hosts
    "limit": 3,                # max harmless copies
    "marker": "STOP",          # presence halts replication
    "logfile": "w_demo.log"
}

RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}
# -------------------- /config -------------------------

logger = logging.getLogger("w_demo")
# Default level; will be set from args in main()
logger.setLevel(logging.INFO)
stream_h = logging.StreamHandler(sys.stdout)
stream_h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(stream_h)

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

def validate_cfg() -> None:
    # Basic type/Value checks
    if not isinstance(CFG.get("limit"), int) or CFG["limit"] < 0:
        raise ValueError("CFG['limit'] must be non-negative int.")
    if not isinstance(CFG.get("host_count"), int) or CFG["host_count"] < 0 or CFG["host_count"] > 10:
        # keep simulated spread small
        raise ValueError("CFG['host_count'] must be 0..10.")
    for k in ("sandbox", "replica_dir", "hosts_root", "marker", "logfile"):
        v = CFG.get(k)
        if v in RESERVED_NAMES or not isinstance(v, str):
            raise ValueError(f"CFG['{k}'] invalid.")
        if any(ch in v for ch in "/\\"):
            raise ValueError(f"CFG['{k}'] must not contain path separators.")
class WormDemo:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.sandbox, self.replicas, self.marker, self.hosts_root = self._paths()
        self._attach_file_logger()

    def _paths(self) -> Tuple[Path, Path, Path, Path]:
        sandbox = Path(self.cfg["sandbox"])
        replicas = sandbox / self.cfg["replica_dir"]
        marker = sandbox / self.cfg["marker"]
        hosts_root = sandbox / self.cfg["hosts_root"]
        return sandbox, replicas, marker, hosts_root
    
    def _attach_file_logger(self):
        try:
            self.sandbox.mkdir(parents=True, exist_ok=True)
            log_path = self.sandbox / self.cfg["logfile"]
            # Guard: only add file handler if not already present
            if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == str(log_path) for h in logger.handlers):
                fh = logging.FileHandler(log_path)
                fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
                logger.addHandler(fh)
                logger.info(f"Log file: {log_path}")
        except Exception as e:
            logger.warning(f"File logger not attached: {e}")
            logger.warning(f"File logger not attached: {e}")

    def init(self):
        try:
            self.sandbox.mkdir(parents=True, exist_ok=True)
            (self.sandbox / "manifest.json").write_text(json.dumps({
            "purpose": "Training-only harmless self-replication demo",
            "safety": {"network": False, "persistence": False, "privilege_escalation": False},
                "limit": self.cfg["limit"],
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            }, indent=2))
            if not self.marker.exists():
                self.marker.write_text(
                    f"This STOP file prevents replication. Remove it to allow up to "
                    f"{self.cfg['limit']} harmless copies.\n"
                )
            # Prepare mock hosts for simulated spread
            (self.hosts_root).mkdir(parents=True, exist_ok=True)
            for i in range(1, self.cfg["host_count"] + 1):
                (self.hosts_root / f"host_{i}" / self.cfg["replica_dir"]).mkdir(parents=True, exist_ok=True)
            logger.info(f"Sandbox ready at ./{self.sandbox}. {C_OK}STOP present.{C_RST}")
        except (OSError, IOError) as e:
            logger.error(f"Init failed: {e}"); sys.exit(1)

    def _atomic_write(self, src: Path, dst: Path):
        dst.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=dst.parent, delete=False) as tf:
            tmp = Path(tf.name)
            with src.open("rb") as s, tmp.open("wb") as d:
                shutil.copyfileobj(s, d)
        os.replace(tmp, dst)

    def _make_polymorph(self, base_bytes: bytes) -> bytes:
        # Append an unused comment banner to alter checksum harmlessly
        banner = f"\n# POLY:{random.randint(10_000, 99_999)} unused comment to vary hash\n"
        return base_bytes + banner.encode("utf-8")

    def _payload(self, target_dir: Path):
        try:
            (target_dir / "friendly_note.txt").write_text(
                "Hello from the harmless demo payload. Stay safe.\n"
            )
            logger.info(f"Payload note written at {target_dir/'friendly_note.txt'}")
        except Exception as e:
            logger.warning(f"Payload write failed: {e}")

    def _replica_name(self, idx: int) -> str:
        return f"w_copy_{idx}.py"

    def _next_index(self) -> int:
        existing = sorted(self.replicas.glob("w_copy_*.py"))
        return len(existing) + 1

    def demo(self, polymorph=False, simulate_spread=False, payload=False):
        if not self.sandbox.exists():
            logger.error("Sandbox not initialized. Run --init first."); sys.exit(2)
        if self.marker.exists():
            logger.info("STOP present; replication blocked."); return

        idx = self._next_index()
        try:
            try:
                src_path = Path(__file__).resolve()
            except NameError:
                src_path = Path(sys.argv[0]).resolve()
            dst = (self.replicas / self._replica_name(idx)).resolve()

            if is_within(dst, self.sandbox):
                # Read source once for both normal and polymorph copies
                base = src_path.read_bytes()
                data = self._make_polymorph(base) if polymorph else base
                # Write replica atomically using _atomic_write
                tmp_src = self.sandbox / f".tmp_replica_{idx}.py"
                tmp_src.write_bytes(data)
                self._atomic_write(tmp_src, dst)
                tmp_src.unlink(missing_ok=True)

                logger.info(f"Replicated -> {dst.name}")
                logger.info(f"src sha256={sha256(src_path)}   dst sha256={sha256(dst)}")
                if payload:
                    self._payload(self.replicas)

                # Simulated “spread” into mock hosts
                if simulate_spread and self.cfg["host_count"] > 0:
                    for i in range(1, self.cfg["host_count"] + 1):
                        host_rep_dir = (self.hosts_root / f"host_{i}" / self.cfg["replica_dir"]).resolve()
                        if not is_within(host_rep_dir, self.sandbox):
                            logger.warning("Host path escaped sandbox; skipping.")
                            continue
                        host_dst = host_rep_dir / self._replica_name(idx)
                        tmp_host_src = self.sandbox / f".tmp_host_{i}_{idx}.py"
                        tmp_host_src.write_bytes(data)
                        self._atomic_write(tmp_host_src, host_dst)
                        tmp_host_src.unlink(missing_ok=True)
                        logger.info(f"(simulated) spread -> host_{i}/{self.cfg['replica_dir']}/{host_dst.name}")
                        if payload:
                            self._payload(host_rep_dir)
            else:
                logger.error("Replica destination escaped sandbox; replication aborted.")
        except (OSError, IOError) as e:
            logger.error(f"Replication failed: {e}"); sys.exit(4)

    def status(self):
        if not self.sandbox.exists():
            print("Status: sandbox not initialized."); return
        copies = sorted(self.replicas.glob("w_copy_*.py")) if self.replicas.exists() else []
        if COLORAMA_AVAILABLE:
            print(f"{C_DIM}=== STATUS ==={C_RST}")
            print(f"sandbox: {self.sandbox.resolve()}")
            print(f"STOP present: {C_OK if self.marker.exists() else C_ERR}{self.marker.exists()}{C_RST}")
        else:
            print("=== STATUS ===")
            print(f"sandbox: {self.sandbox.resolve()}")
            print(f"STOP present: {self.marker.exists()}")
            print(f"limit: {self.cfg['limit']}")
            print(f"replicas: {len(copies)}")
            for c in copies:
                print(f" - {c.name}  sha256={sha256(c)}")
            # hosts summary
            if self.hosts_root.exists():
                host_dirs = sorted(self.hosts_root.glob("host_*"))
                print("hosts:")
                for h in host_dirs:
                    rep = h / self.cfg["replica_dir"]
                    count = len(list(rep.glob("w_copy_*.py"))) if rep.exists() else 0
                    print(f" - {h.name}: {count} replicas")

    def cleanup(self):
        try:
            # Recreate STOP and remove replicas & mock hosts
            self.marker.write_text("STOP\n")
            if self.replicas.exists():
                shutil.rmtree(self.replicas)
            if self.hosts_root.exists():
                shutil.rmtree(self.hosts_root)
                self.hosts_root.mkdir(parents=True, exist_ok=True)
            logger.info("Cleanup done. STOP restored.")
        except (OSError, IOError) as e:
            logger.error(f"Cleanup failed: {e}"); sys.exit(5)

def parse_args():
    p = argparse.ArgumentParser(description="Harmless worm-behavior demo (training only).")
    p.add_argument("--init", action="store_true", help="Prepare sandbox and safety files.")
    p.add_argument("--demo", action="store_true", help="Perform one safe replication (if STOP removed).")
    p.add_argument("--status", action="store_true", help="Show sandbox/replica status.")
    p.add_argument("--cleanup", action="store_true", help="Remove replicas and restore STOP.")
    p.add_argument("--polymorph", action="store_true", help="Change checksum via unused comment.")
    p.add_argument("--simulate-spread", action="store_true", help="Copy into mock hosts within sandbox.")
    p.add_argument("--payload", action="store_true", help="Write harmless note alongside replicas.")
    p.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO",
                   help="Set logging level (default: INFO).")
    return p.parse_args()

def main():
    args = parse_args()
    # Set logging level from argument
    logger.setLevel(getattr(logging, args.log_level.upper(), logging.INFO))

    try:
        validate_cfg()
    except Exception as e:
        logger.error(f"Configuration error: {e}"); sys.exit(10)

    demo = WormDemo(CFG)

    if args.init:
        demo.init()
    elif args.demo:
        demo.demo(polymorph=args.polymorph, simulate_spread=args.simulate_spread, payload=args.payload)
    elif args.status:
        demo.status()
    elif args.cleanup:
        demo.cleanup()
    else:
        # default help
        print("Available flags: --init --demo --status --cleanup --polymorph --simulate-spread --payload")
        print("Example: python replicant_v1.2.py --demo --polymorph --simulate-spread --payload")

if __name__ == "__main__":
    main()