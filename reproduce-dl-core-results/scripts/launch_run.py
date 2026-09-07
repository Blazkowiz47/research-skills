#!/usr/bin/env python3
"""Run an authorized command in an explicit project and retain its execution record."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tempfile


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_record(path: Path, record: dict) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write((json.dumps(record, indent=2) + "\n").encode("utf-8"))
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def stop_child(child: subprocess.Popen | None) -> None:
    if child is None or child.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(child.pid, signal.SIGTERM)
        else:
            child.terminate()
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(child.pid, signal.SIGKILL)
        else:
            child.kill()
        child.wait()
    except ProcessLookupError:
        child.wait()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--record", required=True, type=Path, help="New JSON execution record; companion .log captures combined output.")
    parser.add_argument("--contract", type=Path, help="Existing JSON reproduction contract to embed in this run record.")
    parser.add_argument("--cuda-visible-devices", help="Explicit allocation override; omission preserves the inherited allocation.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    project = args.project.expanduser().resolve()
    if not args.project.expanduser().is_absolute() or not project.is_dir():
        parser.error("--project must be an existing absolute directory")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide a command after --")
    record_path = args.record if args.record.is_absolute() else project / args.record
    log_path = record_path.with_suffix(".log")
    if record_path == log_path or any(p.exists() or p.is_symlink() for p in (record_path, log_path)):
        parser.error("record and companion log must be distinct new files")
    contract = None
    if args.contract:
        contract_path = args.contract if args.contract.is_absolute() else project / args.contract
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        if not isinstance(contract, dict):
            parser.error("contract must be a JSON object")
    environment = os.environ.copy()
    if args.cuda_visible_devices is not None:
        environment["CUDA_VISIBLE_DEVICES"] = args.cuda_visible_devices
    record = {
        "project": str(project), "command": command, "contract": contract,
        "cuda_visible_devices": environment.get("CUDA_VISIBLE_DEVICES"),
        "started_at": None, "finished_at": None, "exit_code": None,
    }
    if args.dry_run:
        print(json.dumps({"preview": record}, indent=2))
        return 0
    record_path.parent.mkdir(parents=True, exist_ok=True)
    # Reserve the output names before starting any external work.
    with record_path.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
    child = None
    old_handler = signal.getsignal(signal.SIGTERM)
    def terminate(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, terminate)
    try:
        with log_path.open("x", encoding="utf-8") as log:
            record["started_at"] = timestamp()
            write_record(record_path, record)
            print(f"Started {record['started_at']}: {shlex.join(command)}", flush=True)
            child = subprocess.Popen(command, cwd=project, env=environment,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, errors="replace", bufsize=1,
                                     start_new_session=os.name == "posix")
            record["pid"] = child.pid
            write_record(record_path, record)
            assert child.stdout is not None
            for line in child.stdout:
                print(line, end="", flush=True)
                log.write(line)
                log.flush()
            record["exit_code"] = child.wait()
    except KeyboardInterrupt:
        stop_child(child)
        record["exit_code"] = 130
        record["error"] = "Launcher interrupted"
    except OSError as exc:
        stop_child(child)
        record["exit_code"] = 127
        record["error"] = str(exc)
    finally:
        signal.signal(signal.SIGTERM, old_handler)
        if child is not None and child.stdout is not None:
            child.stdout.close()
        record["finished_at"] = timestamp()
        write_record(record_path, record)
        print(f"Finished {record['finished_at']}; exit {record['exit_code']}", flush=True)
    code = record["exit_code"]
    return code if code >= 0 else 128 - code


if __name__ == "__main__":
    raise SystemExit(main())
