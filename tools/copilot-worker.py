#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Optional GitHub Copilot CLI 1.0.95 Balanced (Auto) routine-proposal worker.

Text proposals only: no model tools, patch execution or retry. The parent shell
and the native credential store stay trusted_host; this is not a sandbox.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

VERSION = "1.0.95"
PROMPT_BYTES = 1048576
OUTPUT_BYTES = 8388608
META_BYTES = 1048576
KEEP_ENV = ("COPILOT_HOME", "COPILOT_GITHUB_TOKEN")
MCP_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
# The proposal role needs no model tool; view is the smallest non-empty allowlist.
AVAILABLE = ("view",)
EXCLUDED = ("task", "list_agents", "read_agent", "write_agent", "skill", "ask_user")
DENIED = ("read", "write", "shell", "url", "memory")


class Refusal(Exception):
    pass


def date():
    return subprocess.check_output(["date", "-Is"], text=True, timeout=5).strip()


def read_regular(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= limit:
            raise Refusal("invalid_or_oversized_file")
        data = source.read(limit + 1)
        if len(data) > limit:
            raise Refusal("invalid_or_oversized_file")
    data.decode("utf-8", errors="strict")
    if b"\0" in data:
        raise Refusal("invalid_utf8_task")
    return data


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("nonfinite JSON")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def route_environment(providers, inherited=None):
    """Native auth and home only; no inherited Copilot, provider or Git routing."""
    env = {k: v for k, v in (os.environ if inherited is None else inherited).items()
           if not (k.startswith("COPILOT_") or k.startswith("GIT_")) or k in KEEP_ENV}
    env["COPILOT_PROVIDERS_CONFIG"] = str(providers)
    return env


def private_file(path, data):
    with open(path, "xb") as out:
        os.chmod(path, 0o600)
        out.write(data)


def exited(child):
    """Leader exit without reaping, so its process-group id cannot be reused yet."""
    try:
        return os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
    except ChildProcessError:
        return True


def stop_group(child):
    # Signal only this invocation's own new process group, including descendants.
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(child.pid, sig)
        except ProcessLookupError:
            return
        if sig == signal.SIGTERM:
            time.sleep(.1)


def owned_call(argv, env, seconds, cwd=None, data=b"", sinks=(None, None), output_limit=OUTPUT_BYTES):
    """Bound owned process-group lifetime and combined output; feed data via stdin."""
    child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True, umask=0o077)
    poll = selectors.DefaultSelector()
    streams = {child.stdout: 0, child.stderr: 1}
    for pipe in streams:
        poll.register(pipe, selectors.EVENT_READ)
    if data:
        os.set_blocking(child.stdin.fileno(), False)
        poll.register(child.stdin, selectors.EVENT_WRITE)
    else:
        child.stdin.close()
    deadline = time.monotonic() + seconds
    view, sent, seen, stopped = memoryview(data), 0, 0, False
    capture = (bytearray(), bytearray())
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Refusal("timeout")
            if not stopped and exited(child):
                # Descendants must not outlive the native parent or hold its pipes.
                stop_group(child)
                stopped = True
            if not poll.get_map():
                if stopped:
                    break
                time.sleep(min(remaining, .05))
                continue
            for key, _ in poll.select(min(remaining, .2)):
                if key.fileobj is child.stdin:
                    try:
                        sent += os.write(child.stdin.fileno(), view[sent:sent + 65536])
                    except BrokenPipeError:
                        sent = len(data)
                    if sent >= len(data):
                        poll.unregister(child.stdin)
                        child.stdin.close()
                    continue
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    poll.unregister(key.fileobj)
                    continue
                seen += len(chunk)
                if seen > output_limit:
                    raise Refusal("output_limit")
                index = streams[key.fileobj]
                if sinks[index] is None:
                    capture[index].extend(chunk)
                else:
                    sinks[index].write(chunk)
        return child.wait(timeout=5), bytes(capture[0]), bytes(capture[1])
    finally:
        poll.close()
        if child.returncode is None:
            stop_group(child)
        for pipe in (child.stdin, child.stdout, child.stderr):
            pipe.close()
        child.wait(timeout=5)


def metadata(cli, env, cwd, *command):
    return owned_call([cli, "--no-auto-update", *command], env, 60, cwd, output_limit=META_BYTES)


def auto_fallback_setting(cli, env, cwd):
    code, out, err = metadata(cli, env, cwd, "config", "continueOnAutoMode")
    value = out.decode("utf-8", errors="replace").strip()
    if code == 1 and not value and not err.strip():
        return "unset"
    if code == 0 and value == "false":
        return "false"
    raise Refusal("auto_fallback_enabled" if code == 0 and value == "true" else "unrecognized_auto_fallback_setting")


def refuse_plugins(cli, env, cwd):
    code, out, _ = metadata(cli, env, cwd, "plugin", "list", "--json")
    try:
        plugins = strict_json(out) if code == 0 else None
    except (ValueError, UnicodeError, RecursionError):
        plugins = None
    if not isinstance(plugins, list):
        raise Refusal("invalid_plugin_metadata")
    if plugins:
        raise Refusal("plugins_present")


def refuse_extensions(env):
    home = Path(env["COPILOT_HOME"]) if env.get("COPILOT_HOME") else Path.home() / ".copilot"
    path = home / "extensions"
    if os.path.lexists(path) and (path.is_symlink() or not path.is_dir() or any(path.iterdir())):
        raise Refusal("extensions_present")


def mcp_names(cli, env, cwd):
    """Server names only; raw MCP configuration and headers are never kept."""
    code, out, _ = metadata(cli, env, cwd, "mcp", "list", "--json")
    try:
        value = strict_json(out) if code == 0 else None
    except (ValueError, UnicodeError, RecursionError):
        value = None
    servers = value.get("mcpServers", {}) if isinstance(value, dict) else None
    if not isinstance(servers, dict) or len(servers) > 64:
        raise Refusal("invalid_mcp_metadata")
    if not all(isinstance(name, str) and MCP_NAME.fullmatch(name) for name in servers):
        raise Refusal("invalid_mcp_metadata")
    return sorted(servers)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    def interrupted(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-file", help="Regular UTF-8 task with all selected context inline; otherwise TASKFILE")
    parser.add_argument("--receipt-dir", required=True, help="Existing private parent; each invocation creates a new run")
    parser.add_argument("--time-limit", type=float, default=900)
    parser.add_argument("--max-ai-credits", type=int, default=30, help="Native soft cap, 30..300")
    args = parser.parse_args()
    record = None
    receipt = None
    started = time.monotonic()
    exit_code = 2
    try:
        if not math.isfinite(args.time_limit) or not 0 < args.time_limit <= 7200:
            raise Refusal("invalid_bounds")
        if not 30 <= args.max_ai_credits <= 300:
            raise Refusal("invalid_bounds")
        prompt = args.prompt_file or os.environ.get("TASKFILE")
        if not prompt:
            raise Refusal("missing_task")
        data = read_regular(prompt, PROMPT_BYTES)
        parent = Path(args.receipt_dir).absolute()
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise Refusal("receipt_parent_must_be_private")
        cli = shutil.which("copilot")
        git = shutil.which("git")
        if not cli or not git:
            raise Refusal("missing_cli")
        cli = os.path.realpath(cli)
        env = route_environment(parent / "unused-providers.json")
        code, version, _ = owned_call([cli, "--no-auto-update", "--version"], env, 30, parent, output_limit=4096)
        lines = version.decode("utf-8", errors="replace").strip().splitlines()
        # Later lines may announce an update; only the first identifies the binary.
        if code or not lines or lines[0].strip() != "GitHub Copilot CLI " + VERSION:
            raise Refusal("unsupported_cli")
        directory = Path(tempfile.mkdtemp(prefix="copilot-run-", dir=parent))
        receipt = directory / "receipt.json"
        proposal = directory / "proposal.md"
        usage = directory / "usage.json"
        stderr_path = directory / "native-stderr.log"
        record = dict(schema_version=1, started_at=date(), role="routine_proposal",
                      transport="GitHub Copilot CLI", cli_version=VERSION, cli_sha256=file_sha256(cli),
                      task_sha256=hashlib.sha256(data).hexdigest(), task_bytes=len(data), prompt_transport="stdin",
                      budget_group="copilot", subscription="owner_reported_free", remaining_allowance="unknown",
                      requested_route=dict(name="Balanced", model="auto", auto_tier="balance"),
                      requested_effort="medium", effective_model="unknown", effective_ai_lab="unknown",
                      effective_effort="unknown",
                      native_limits=dict(max_ai_credits=args.max_ai_credits, max_ai_credits_kind="soft_post_response",
                                         time_limit=args.time_limit),
                      trust=dict(parent_shell="trusted_host", native_credentials="trusted_host", sandbox=False),
                      invocations=0, invocation_retries=0, fallback_route="none", native_exit=None,
                      outcome="preflight", proposal_path=str(proposal), usage_path=str(usage),
                      stderr_path=str(stderr_path))
        receipt.write_text(json.dumps(record, indent=2) + "\n")
        work = directory / "work"
        template = directory / "git-template"
        work.mkdir(mode=0o700)
        template.mkdir(mode=0o700)
        settings = work / ".github" / "copilot"
        settings.mkdir(parents=True)
        private_file(settings / "settings.json", b'{"disableAllHooks": true}\n')
        providers = directory / "providers.json"
        private_file(providers, b'{"providers": {}, "models": {}}\n')
        env = route_environment(providers)
        # A neutral repository bounds native parent-repository discovery.
        code, _, _ = owned_call([git, "init", "--quiet", "--template=" + str(template), str(work)],
                                env, 30, directory, output_limit=65536)
        if code:
            raise Refusal("git_init_failed")
        record["continue_on_auto_mode"] = auto_fallback_setting(cli, env, work)
        refuse_plugins(cli, env, work)
        refuse_extensions(env)
        names = mcp_names(cli, env, work)
        record.update(plugins=0, extensions="none", disabled_mcp_servers=names, builtin_mcps="disabled",
                      model_tools=dict(available=list(AVAILABLE), excluded=list(EXCLUDED), denied=list(DENIED)))
        argv = [cli, "--no-auto-update", "--model", "auto", "--auto-tier", "balance", "--effort", "medium",
                "--max-ai-credits", str(args.max_ai_credits), "--usage-output-file", str(usage),
                "--log-dir", str(directory / "native-logs"), "--log-level", "none", "--stream", "off", "--silent",
                "--no-custom-instructions", "--no-ask-user", "--no-experimental", "--no-bash-env",
                "--no-remote", "--no-remote-export", "--disable-builtin-mcps",
                "--secret-env-vars=" + ",".join(KEEP_ENV + ("GH_TOKEN", "GITHUB_TOKEN"))]
        for name in names:
            argv.append("--disable-mcp-server=" + name)
        argv.extend("--available-tools=" + name for name in AVAILABLE)
        argv.extend("--excluded-tools=" + name for name in EXCLUDED)
        argv.extend("--deny-tool=" + name for name in DENIED)
        # Required for non-interactive mode; deny rules still take precedence.
        argv.append("--allow-all-tools")
        record.update(invocations=1, outcome="starting")
        receipt.write_text(json.dumps(record, indent=2) + "\n")
        with open(proposal, "xb") as out, open(stderr_path, "xb") as err:
            os.chmod(proposal, 0o600)
            os.chmod(stderr_path, 0o600)
            code, _, _ = owned_call(argv, env, args.time_limit, work, data, (out, err))
        record["native_exit"] = code
        try:
            read_regular(usage, META_BYTES)
            strict_json(usage.read_bytes())
            record["usage_state"] = "recorded_not_remaining_allowance"
        except (OSError, ValueError, UnicodeError, Refusal, RecursionError):
            record["usage_state"] = "invalid_or_missing"
        record["proposal_bytes"] = proposal.stat().st_size
        if code:
            record["outcome"], exit_code = "native_failed", 1
        else:
            try:
                text = read_regular(proposal, OUTPUT_BYTES).decode("utf-8")
            except (OSError, UnicodeError, Refusal):
                text = ""
            if text.strip():
                record["outcome"], exit_code = "proposal_recorded", 0
            else:
                record["outcome"], exit_code = "empty_or_invalid_response", 2
    except KeyboardInterrupt:
        exit_code = 130
        if record is not None:
            record["outcome"] = "interrupted"
    except (Refusal, OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
        state = str(error) if isinstance(error, Refusal) else "local_failure"
        if record is not None:
            record["outcome"] = state
        print("Copilot adapter: " + state, file=sys.stderr)
        exit_code = 124 if state == "timeout" else 2
    finally:
        if record is not None:
            record.update(adapter_exit=exit_code, elapsed_seconds=round(time.monotonic() - started, 3), finished_at=date())
            receipt.write_text(json.dumps(record, indent=2) + "\n")
            print(json.dumps({"receipt": str(receipt), "adapter_exit": exit_code, "native_exit": record["native_exit"],
                              "outcome": record["outcome"], "proposal": record["proposal_path"]}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
