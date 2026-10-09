#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Offline real-schema-shaped CLI fixtures; no Vibe inference or network."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/vibe-worker.py"
spec = importlib.util.spec_from_file_location("vibe_worker", SCRIPT)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
FAKE = r'''
import json,os,pathlib,sys,time
if sys.argv[1:]==['--version']:
 print('vibe '+os.environ.get('FAKE_VERSION','2.26.1'));raise SystemExit()
a=sys.argv[1:]
pathlib.Path(os.environ['MARKER']).open('a').write('call\n')
assert '-p' not in a and '--auto-approve' not in a
get=lambda k:a[a.index(k)+1]
assert get('--agent')=='auto-approve' and '--trust' in a
label=os.environ['VIBE_ACTIVE_MODEL'];model=json.loads(os.environ['VIBE_MODELS'])[label]
wire='zai-glm-5-3' if label=='glm-5-3' else 'mistral-medium-3-5'
assert model['name']==wire and model['alias']==label and model['provider']=='mistral'
assert model['thinking']=='high' and model['thinking_levels']==['high']
assert model['input_price']>0 and model['output_price']>0
assert json.loads(os.environ['VIBE_ALLOWED_MODELS'])==[wire]
assert json.loads(os.environ['VIBE_COMPACTION_MODEL'])==model
assert json.loads(os.environ['VIBE_UTILITY_MODELS'])=={'title':'active','smart_approve':'active'}
for key in ['VIBE_SESSION_LOGGING__GENERATE_TITLES','VIBE_ENABLE_UPDATE_CHECKS','VIBE_ENABLE_AUTO_UPDATE','VIBE_EXPERIMENTS__ENABLE','VIBE_ENABLE_SUBAGENTS','VIBE_ENABLE_CONNECTORS']:
 assert os.environ[key]=='false'
assert json.loads(os.environ['VIBE_MCP_SERVERS'])==[]
assert os.environ['VIBE_API_RETRY_MAX_ELAPSED_TIME']=='0'
assert 'VIBE_INVENTED_OVERRIDE' not in os.environ
assert get('--max-tokens')==os.environ.get('EXPECT_TOKENS','2000000')
assert float(get('--max-price'))==float(os.environ.get('EXPECT_PRICE','5'))
assert [a[i+1] for i,v in enumerate(a) if v=='--enabled-tools']==['bash','read_file','write_file','edit','grep']
content=pathlib.Path(get('--prompt-file')).read_text()
assert len(content)==int(os.environ['EXPECT_PROMPT_LENGTH'])
assert content not in ' '.join(a)
mode=os.environ.get('FAKE_MODE','ok');code=int(os.environ.get('FAKE_EXIT','0'))
if mode=='missing':raise SystemExit(code)
x={'schema_version':1,'vibe_version':'2.26.1','outcome':'finished' if code==0 else 'token_limit','stop_reason':None if code==0 else 'interrupted','exit_code':code,'usage':{'input_tokens':198950,'output_tokens':2336,'cached_input_tokens':0,'total_tokens':201286},'cost_usd':.2888084,'config':{'secret':'NEVER-IN-RECEIPT'},'error':{'message':'NEVER-IN-RECEIPT'}}
if mode=='nan':x['cost_usd']=float('nan')
if mode=='bool':x['usage']['input_tokens']=True
if mode=='legacy':x['usage']={'prompt_tokens':1,'completion_tokens':2,'total_tokens':3}
if mode=='none':x['usage']=None;x['cost_usd']=None
if mode=='unsafe_reason':x['stop_reason']='NEVER-IN-RECEIPT'
text=json.dumps(x)
if mode=='duplicate':text=text.replace('"schema_version": 1','"schema_version": 1, "schema_version": 1')
pathlib.Path(get('--output-dir'),'export.json').write_text(text)
print('NEVER-IN-RECEIPT')
print('NEVER-IN-RECEIPT',file=sys.stderr)
raise SystemExit(code)
'''


class VibeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-offline-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prompt = self.root / "large task with spaces.md"
        self.prompt.write_text("a" * 150000)
        self.receipts = self.root / "private receipts"
        self.receipts.mkdir(mode=0o700)
        cli = self.root / "vibe"
        cli.write_text("#!" + sys.executable + "\n" + FAKE)
        cli.chmod(0o700)
        self.marker = self.root / "calls"
        self.env = dict(os.environ, PATH=str(self.root)+os.pathsep+os.environ['PATH'],
                        MARKER=str(self.marker), EXPECT_PROMPT_LENGTH="150000",
                        VIBE_ACTIVE_MODEL="wrong", VIBE_INVENTED_OVERRIDE="wrong")

    def invoke(self, *args, **env):
        return subprocess.run([sys.executable,"-B",str(SCRIPT),"--model","glm-5-3",
                               "--prompt-file",str(self.prompt),"--receipt-dir",str(self.receipts),*args],
                              env=dict(self.env,**env),capture_output=True,text=True,timeout=30)

    def receipt(self):
        paths=list(self.receipts.glob('vibe-run-*/receipt.json'))
        self.assertEqual(len(paths),1)
        return json.loads(paths[0].read_text())

    def test_exact_pins_actual_usage_private_transport_and_one_call(self):
        p=self.invoke()
        self.assertEqual(p.returncode,0,p.stderr)
        r=self.receipt()
        self.assertEqual(r['export']['usage']['input_tokens'],198950)
        self.assertEqual(r['export']['estimated_cost_usd'],.2888084)
        self.assertEqual(r['native_limits']['max_tokens'],2000000)
        self.assertEqual(r['budget_group'],'mistral')
        self.assertEqual(r['effective_model'],'unknown')
        self.assertEqual(self.marker.read_text(),'call\n')
        self.assertNotIn('NEVER-IN-RECEIPT',json.dumps(r)+p.stdout+p.stderr)

    def test_second_model_and_substantial_budget(self):
        p=self.invoke('--model','mistral-medium-3-5','--max-tokens','4000000','--max-price','10',
                      EXPECT_TOKENS='4000000',EXPECT_PRICE='10')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(self.receipt()['configured_wire_model'],'mistral-medium-3-5')

    def test_native_limit_exit_three_is_not_provider_exhaustion(self):
        p=self.invoke(FAKE_EXIT='3')
        self.assertEqual(p.returncode,3,p.stderr)
        r=self.receipt()
        self.assertEqual(r['process_exit'],3)
        self.assertEqual(r['export']['outcome'],'token_limit')
        self.assertEqual(r['remaining_allowance'],'unknown')
        self.assertEqual(self.marker.read_text(),'call\n')

    def test_missing_or_malformed_export_cannot_report_success(self):
        for mode in ['missing','nan','bool','legacy','duplicate','unsafe_reason']:
            with self.subTest(mode=mode):
                p=self.invoke(FAKE_MODE=mode)
                self.assertEqual(p.returncode,2,p.stderr)
                latest=json.loads(sorted(self.receipts.glob('vibe-run-*/receipt.json'),key=lambda p:p.stat().st_mtime_ns)[-1].read_text())
                self.assertEqual(latest['export_state'],'invalid_or_missing')
                self.assertNotIn('NEVER-IN-RECEIPT',json.dumps(latest))

    def test_missing_usage_remains_unknown_not_zero(self):
        p=self.invoke(FAKE_MODE='none')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIsNone(self.receipt()['export']['usage'])
        self.assertIsNone(self.receipt()['export']['estimated_cost_usd'])

    def test_invalid_bounds_unknown_model_and_unsupported_version_pre_call(self):
        for args in [('--max-price','nan'),('--max-price','inf'),('--max-tokens','0'),
                     ('--max-turns','0'),('--time-limit','nan'),('--model','wrong')]:
            with self.subTest(args=args):self.assertNotEqual(self.invoke(*args).returncode,0)
        self.assertNotEqual(self.invoke(FAKE_VERSION='2.0.0').returncode,0)
        self.assertFalse(self.marker.exists())
        self.assertFalse(list(self.receipts.iterdir()))

    def test_new_receipts_never_overwrite_and_taskfile_fallback(self):
        first=self.invoke();self.assertEqual(first.returncode,0,first.stderr)
        path=next(self.receipts.glob('vibe-run-*/receipt.json'));before=path.read_bytes()
        p=self.invoke('--prompt-file','',TASKFILE=str(self.prompt))
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(path.read_bytes(),before)
        self.assertEqual(len(list(self.receipts.glob('vibe-run-*'))),2)

    def test_unsafe_task_files_are_refused_before_provider(self):
        self.prompt.unlink();os.mkfifo(self.prompt)
        self.assertNotEqual(self.invoke().returncode,0)
        self.prompt.unlink();self.prompt.symlink_to(__file__)
        self.assertNotEqual(self.invoke().returncode,0)
        self.assertFalse(self.marker.exists())

    def test_owned_deadline_output_bound_and_unrelated_process_survives(self):
        other=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'])
        self.addCleanup(lambda:other.poll() is None and other.kill())
        with self.assertRaises(worker.Refusal):
            worker.owned_call([sys.executable,'-c','import time;time.sleep(10)'],dict(os.environ),.1)
        with self.assertRaises(worker.Refusal):
            worker.owned_call([sys.executable,'-c','print("x"*10000)'],dict(os.environ),2,output_limit=20)
        self.assertIsNone(other.poll())
        other.terminate();other.wait(timeout=3)


if __name__=='__main__':
    unittest.main()
