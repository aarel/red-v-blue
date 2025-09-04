Red vs. Blue Project

⚠️ For Training and Education Only
This repository contains a harmless, sandboxed demonstration of worm-like and Trojan-like behaviors for security training.
It never touches real networks, registry, autoruns, or system files.
All activity is confined to ./sandbox_w/ and removable with --cleanup.

Purpose

This project was built to support Red Team vs. Blue Team exercises, showing how offensive tactics (Red) and defensive controls (Blue) intersect.
It is aligned with CWE-506 / CWE-507, OWASP Testing Guide, and NIST SP 800-83r1 — making it appropriate for professional training and compliance-oriented scenarios.

Features by Version
v1.x — Foundations

Basic Red vs. Blue drills: Bluetooth scanning, packet sniffing, password spraying, VPN logins.

Initial worm demo: simple self-replication in a folder (no network, no persistence).

Trojan demo: harmless “calculator” app that secretly logs usage.

v2.0–v2.2 — Hardening

Error handling, structured logging, atomic file copies.

Config validation (sandbox only, no path traversal).

STOP kill-switch and cleanup subcommand.

Sandbox manifest + safety metadata.

v2.3 — Advanced Simulation

Polymorphism: alters checksums with unused comments.

Simulated spread: replicates into mock host folders (local only).

Harmless payload: drops a friendly_note.txt.

Recovery: journaled two-phase commit, cleans up failed runs.

Resource guards: free disk/memory checks.

Concurrency safety: single-instance lock to prevent race conditions.

Full repo scaffolding: src/, tests/, requirements.txt, pytest harness.

v2.4 — Extended Realism (still safe)

Obfuscation+: adds junk code and unused stubs.

Stealth alias logging: fake process names written to telemetry.

Mock persistence: writes a non-executable marker file under mock_startup/.

Simulated networking: logs connection attempts (no sockets).

Config editing: --config-edit key=value, --save-config.

Enhanced README, Threat→Control tables, CHANGELOG, and references.

| Simulated Behavior         | Red Demonstrates             | Blue Control / Lesson                  |
| -------------------------- | ---------------------------- | -------------------------------------- |
| Self-replication           | Copies inside sandbox        | File integrity monitoring (FIM)        |
| -------------------------- | ---------------------------- | -------------------------------------- |
| Polymorphism / Obfuscation | Varying checksums, junk code | Behavior analytics, YARA rules         |
| -------------------------- | ---------------------------- | -------------------------------------- |
| Simulated Spread           | Replicas in mock hosts       | Network segmentation, least privilege  |
| -------------------------- | ---------------------------- | -------------------------------------- |
| Payload                    | Drops note file              | App allowlisting, anomaly alerts       |
| -------------------------- | ---------------------------- | -------------------------------------- |
| Stealth alias              | Fake process name            | EDR process monitoring                 |
| -------------------------- | ---------------------------- | -------------------------------------- |
| Mock persistence           | Startup-like marker file     | Persistence detection, audit trails    |
| -------------------------- | ---------------------------- | -------------------------------------- |
| Simulated networking       | Connect attempt logs         | Proxy/NetFlow logging, egress controls |
| -------------------------- | ---------------------------- | -------------------------------------- |
| Recovery                   | Journal cleanup              | IR playbooks, audit trail              |
| -------------------------- | ---------------------------- | -------------------------------------- |
| Resource/Lock              | Safe execution limits        | Reliability & lab repeatability        |
| -------------------------- | ---------------------------- | -------------------------------------- |

Quick Start
# Setup environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Initialize sandbox
python -m w_demo.w_demo --init
python -m w_demo.w_demo --status

# Run a demo
rm sandbox_w/STOP
python -m w_demo.w_demo --demo --polymorph --simulate-spread --payload

# Advanced demo
python -m w_demo.w_demo --demo --obfuscate-plus --stealth --mock-persist --simulate-net

# Cleanup
python -m w_demo.w_demo --cleanup

Testing

Pytest suite included:

pytest -q


Covers STOP enforcement, replication limits, polymorphism changes, recovery cleanup, stealth/persistence/network simulations.

References

NIST SP 800-83r1 – Malware Incident Prevention & Handling

CWE-506 / CWE-507 – Embedded Malicious Code, Trojan Horse

OWASP Testing Guide – Behavioral testing, anti-pattern analysis

License

MIT License – for training and educational use only.
