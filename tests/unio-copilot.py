#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Offline fake-CLI checks; no real Copilot CLI, authentication, config or model."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/copilot-worker.py"
spec = importlib.util.spec_from_file_location("copilot_worker", SCRIPT)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
SECRET = "NEVER-IN-RECEIPT"
FAKE = r'''
import hashlib,json,os,pathlib,subprocess,sys,time
a=sys.argv[1:]
assert a[0]=='--no-auto-update',a
a=a[1:]
mode=os.environ.get('FAKE_MODE','ok')
if a==['--version']:
 print('GitHub Copilot CLI '+os.environ.get('FAKE_VERSION','1.0.95')+'.')
 print('A newer version 9.9.9 is available.');raise SystemExit()
if a==['config','continueOnAutoMode']:
 v=os.environ.get('FAKE_CONTINUE','unset')
 if v=='unset':raise SystemExit(1)
 print(v);raise SystemExit()
if a==['plugin','list','--json']:
 print(os.environ.get('FAKE_PLUGINS','[]'));raise SystemExit()
if a==['mcp','list','--json']:
 names=json.loads(os.environ.get('FAKE_MCP','["alpha","beta.tools"]'))
 print(json.dumps({'mcpServers':{n:{'type':'http','url':'https://example.invalid','headers':{'Authorization':'Bearer NEVER-IN-RECEIPT'},'enabled':True} for n in names}}));raise SystemExit()
pathlib.Path(os.environ['MARKER']).open('a').write('call\n')
e=os.environ
for k in ['COPILOT_MODEL','COPILOT_OFFLINE','COPILOT_ALLOW_ALL','COPILOT_PROVIDER_BASE_URL','COPILOT_INVENTED','COPILOT_AGENT_MODEL','GIT_DIR']:
 assert k not in e,k
assert e['COPILOT_HOME']==e['EXPECT_HOME'] and e['COPILOT_GITHUB_TOKEN']=='auth-only'
assert json.loads(pathlib.Path(e['COPILOT_PROVIDERS_CONFIG']).read_text())=={'providers':[],'models':[]}
cwd=pathlib.Path.cwd()
assert (cwd/'.git').is_dir() and not list((cwd/'.git'/'hooks').glob('*'))
assert json.loads((cwd/'.github/copilot/settings.json').read_text())=={'disableAllHooks':True}
get=lambda k:a[a.index(k)+1]
assert get('--model')=='auto' and get('--auto-tier')=='balance'
assert '--reasoning-effort' not in a and '--effort' not in a
assert get('--max-ai-credits')==e.get('EXPECT_CREDITS','30') and get('--stream')=='off' and get('--log-level')=='none'
for f in ['--no-custom-instructions','--no-ask-user','--no-experimental','--no-bash-env','--no-remote','--no-remote-export','--disable-builtin-mcps','--allow-all-tools','--silent']:
 assert f in a,f
for f in ['-p','--prompt','--resume','--continue','--autopilot','--fleet','--enable-memory','--experimental','--allow-all','--share']:
 assert f not in a,f
vals=lambda p:[x[len(p):] for x in a if x.startswith(p)]
assert vals('--disable-mcp-server=')==json.loads(e['EXPECT_MCP'])
assert vals('--available-tools=')==['view']
assert set(vals('--deny-tool='))=={'read','write','shell','url','memory'}
assert set(vals('--excluded-tools='))>={'task','list_agents','read_agent','write_agent','skill','ask_user'}
task=sys.stdin.buffer.read()
assert hashlib.sha256(task).hexdigest()==e['EXPECT_SHA'],len(task)
assert task.decode() not in ' '.join(a) and max(map(len,a))<4096
pathlib.Path(get('--usage-output-file')).write_text(json.dumps({'totalNanoAiu':5,'note':'not remaining allowance'}))
print('NEVER-IN-RECEIPT',file=sys.stderr)
if mode in ('orphan','hang'):
 kid=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 pathlib.Path(e['KIDFILE']).write_text(str(kid.pid))
if mode=='hang':time.sleep(60)
if mode=='flood':sys.stdout.write('x'*(9*1048576))
if mode not in ('empty','blank'):print('Proposal: rename the helper.')
if mode=='blank':print('   ')
raise SystemExit(int(e.get('FAKE_EXIT','0')))
'''


class CopilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="copilot-offline-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        bindir = self.root / "fake bin"
        bindir.mkdir()
        cli = bindir / "copilot"
        cli.write_text("#!" + sys.executable + "\n" + FAKE)
        cli.chmod(0o700)
        self.prompt = self.root / "large task with spaces.md"
        text = "Übersicht € — routine proposal context.\n" * 15000
        self.prompt.write_text(text, encoding="utf-8")
        self.receipts = self.root / "private receipts"
        self.receipts.mkdir(mode=0o700)
        self.home = self.root / "native home"
        self.home.mkdir()
        self.marker = self.root / "calls"
        self.kidfile = self.root / "kid"
        self.env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ["PATH"],
                        MARKER=str(self.marker), KIDFILE=str(self.kidfile),
                        EXPECT_SHA=hashlib.sha256(text.encode()).hexdigest(),
                        EXPECT_MCP='["alpha", "beta.tools"]',
                        COPILOT_HOME=str(self.home), EXPECT_HOME=str(self.home),
                        COPILOT_GITHUB_TOKEN="auth-only", COPILOT_MODEL="gpt-paid",
                        COPILOT_OFFLINE="true", COPILOT_ALLOW_ALL="true", COPILOT_AGENT_MODEL="local",
                        COPILOT_PROVIDER_BASE_URL="http://127.0.0.1:11434", COPILOT_INVENTED="x",
                        GIT_DIR=str(self.root / "elsewhere"))
        self.env.pop("TASKFILE", None)

    def invoke(self, *args, **env):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "--prompt-file", str(self.prompt),
                               "--receipt-dir", str(self.receipts), *args],
                              env=dict(self.env, **env), capture_output=True, text=True, timeout=60)

    def receipt(self):
        paths = list(self.receipts.glob("copilot-run-*/receipt.json"))
        self.assertEqual(len(paths), 1)
        return json.loads(paths[0].read_text())

    def stored_text(self):
        return "".join(p.read_text(errors="replace") for p in self.receipts.rglob("*")
                       if p.is_file() and p.name != "native-stderr.log")

    def test_balanced_route_stdin_task_and_private_receipt(self):
        p = self.invoke()
        r = self.receipt()
        self.assertEqual(p.returncode, 0, p.stderr + Path(r["stderr_path"]).read_text())
        self.assertEqual(r["outcome"], "proposal_recorded")
        self.assertEqual((r["native_exit"], r["adapter_exit"], r["invocations"], r["invocation_retries"]), (0, 0, 1, 0))
        self.assertEqual(r["requested_route"], dict(name="Balanced", model="auto", auto_tier="balance"))
        self.assertEqual((r["effective_model"], r["effective_effort"], r["remaining_allowance"]), ("unknown",) * 3)
        self.assertEqual(r["fallback_route"], "none")
        self.assertEqual(r["continue_on_auto_mode"], "unset")
        self.assertEqual(r["disabled_mcp_servers"], ["alpha", "beta.tools"])
        self.assertEqual(r["usage_state"], "recorded_not_remaining_allowance")
        self.assertEqual(r["task_sha256"], self.env["EXPECT_SHA"])
        self.assertIn("rename the helper", Path(r["proposal_path"]).read_text())
        for key in ("proposal_path", "usage_path", "stderr_path"):
            self.assertEqual(Path(r[key]).stat().st_mode & 0o077, 0, key)
            self.assertTrue(Path(r[key]).is_relative_to(self.receipts))
        self.assertEqual(self.marker.read_text(), "call\n")
        self.assertNotIn(SECRET, self.stored_text() + p.stdout + p.stderr)
        self.assertNotIn("auth-only", self.stored_text() + p.stdout + p.stderr)

    def test_route_environment_drops_inherited_routing(self):
        env = worker.route_environment(Path("/run/providers.json"), dict(
            COPILOT_HOME="h", COPILOT_GITHUB_TOKEN="t", COPILOT_PROVIDER_TYPE="openai",
            COPILOT_PROVIDERS_CONFIG="/evil.json", COPILOT_MODEL="m", COPILOT_OFFLINE="1",
            GIT_WORK_TREE="/", PATH="/bin", HOME="/home/u"))
        self.assertEqual(env, dict(COPILOT_HOME="h", COPILOT_GITHUB_TOKEN="t", PATH="/bin", HOME="/home/u",
                                   COPILOT_PROVIDERS_CONFIG="/run/providers.json"))

    def test_refusals_before_any_receipt(self):
        for args in [("--max-ai-credits", "29"), ("--max-ai-credits", "301"), ("--time-limit", "0"),
                     ("--time-limit", "7201"), ("--time-limit", "nan")]:
            with self.subTest(args=args):
                self.assertNotEqual(self.invoke(*args).returncode, 0)
        self.assertEqual(self.invoke(FAKE_VERSION="1.0.96").returncode, 2)
        self.receipts.chmod(0o755)
        self.assertEqual(self.invoke().returncode, 2)
        self.receipts.chmod(0o700)
        self.assertFalse(self.marker.exists())
        self.assertFalse(list(self.receipts.iterdir()))

    def test_metadata_refusals_before_prompt(self):
        cases = [(dict(FAKE_PLUGINS='[{"name":"p","enabled":false,"source":"installed"}]'), "plugins_present"),
                 (dict(FAKE_PLUGINS='{"plugins":[]}'), "invalid_plugin_metadata"),
                 (dict(FAKE_CONTINUE="true"), "auto_fallback_enabled"),
                 (dict(FAKE_CONTINUE="maybe"), "unrecognized_auto_fallback_setting"),
                 (dict(FAKE_MCP='["ok", "--allow-all"]'), "invalid_mcp_metadata"),
                 (dict(FAKE_MCP='["has space"]'), "invalid_mcp_metadata")]
        for env, outcome in cases:
            with self.subTest(outcome=outcome, env=env):
                p = self.invoke(**env)
                self.assertEqual(p.returncode, 2, p.stderr)
                latest = max(self.receipts.glob("copilot-run-*/receipt.json"), key=lambda q: q.stat().st_mtime_ns)
                r = json.loads(latest.read_text())
                self.assertEqual((r["outcome"], r["invocations"]), (outcome, 0))
        (self.home / "extensions" / "owner-ext").mkdir(parents=True)
        self.assertEqual(self.invoke().returncode, 2)
        self.assertFalse(self.marker.exists())
        self.assertNotIn(SECRET, self.stored_text())

    def test_nonzero_and_empty_output_are_not_success(self):
        for env, code, outcome in [(dict(FAKE_EXIT="3"), 1, "native_failed"),
                                   (dict(FAKE_MODE="empty"), 2, "empty_or_invalid_response"),
                                   (dict(FAKE_MODE="blank"), 2, "empty_or_invalid_response"),
                                   (dict(FAKE_MODE="flood"), 2, "output_limit")]:
            with self.subTest(outcome=outcome):
                p = self.invoke(**env)
                self.assertEqual(p.returncode, code, p.stderr)
                self.assertEqual(json.loads(p.stdout)["outcome"], outcome)
        self.assertEqual(self.marker.read_text(), "call\n" * 4)

    def test_descendants_reaped_on_parent_exit_and_timeout(self):
        other = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
        self.addCleanup(lambda: (other.kill(), other.wait()))
        for env, args, code in [(dict(FAKE_MODE="orphan"), (), 0), (dict(FAKE_MODE="hang"), ("--time-limit", "2"), 124)]:
            with self.subTest(mode=env["FAKE_MODE"]):
                started = time.monotonic()
                p = self.invoke(*args, **env)
                self.assertEqual(p.returncode, code, p.stderr)
                self.assertLess(time.monotonic() - started, 20)
                kid = int(self.kidfile.read_text())
                time.sleep(.2)
                with self.assertRaises(ProcessLookupError):
                    os.kill(kid, 0)
        self.assertIsNone(other.poll())

    def test_owned_call_feeds_large_stdin_and_bounds_output(self):
        data = ("ü" * 700000).encode()
        code, out, _ = worker.owned_call([sys.executable, "-c", "import sys;sys.stdout.write(str(len(sys.stdin.buffer.read())))"],
                                         dict(os.environ), 10, data=data)
        self.assertEqual((code, out), (0, str(len(data)).encode()))
        with self.assertRaises(worker.Refusal):
            worker.owned_call([sys.executable, "-c", "print('x'*10000)"], dict(os.environ), 5, output_limit=20)


if __name__ == "__main__":
    unittest.main()
