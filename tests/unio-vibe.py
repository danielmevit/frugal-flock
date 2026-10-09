import os
import sys
import unittest
import subprocess
import tempfile
import json
import shutil

class TestVibeWorker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="vibe_test_")
        self.worker_script = os.path.join(os.path.dirname(__file__), "..", "tools", "vibe-worker.py")
        
        self.prompt_file = os.path.join(self.temp_dir, "task with spaces.md")
        with open(self.prompt_file, "w", encoding="utf-8") as f:
            f.write("test prompt\n")
            
        self.receipt_dir = os.path.join(self.temp_dir, "receipt")
        os.makedirs(self.receipt_dir)
        
        # Create a fake vibe executable
        self.fake_vibe_bin = os.path.join(self.temp_dir, "vibe")
        with open(self.fake_vibe_bin, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("if [ \"$1\" = \"--version\" ]; then echo '2.26.1'; exit 0; fi\n")
            # Write a fake export.json to the requested --output-dir
            f.write("for i in \"$@\"; do if [ \"$i\" = \"--output-dir\" ]; then OUTDIR_FLAG=1; elif [ \"$OUTDIR_FLAG\" = \"1\" ]; then OUTDIR=$i; OUTDIR_FLAG=0; fi; done\n")
            f.write("if [ -n \"$OUTDIR\" ]; then echo '{\"schema_version\": \"1.0\", \"outcome\": \"success\", \"stop_reason\": \"limit\", \"usage\": {\"prompt_tokens\": 10, \"completion_tokens\": 20, \"total_tokens\": 30}, \"cost\": {\"total\": 0.05}}' > \"$OUTDIR/export.json\"; fi\n")
            f.write("exit 3\n")
        os.chmod(self.fake_vibe_bin, 0o755)
        
        self.env = os.environ.copy()
        self.env["PATH"] = self.temp_dir + os.pathsep + self.env.get("PATH", "")
        # Inherited bad model
        self.env["VIBE_ACTIVE_MODEL"] = "bad-model-override-me"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_successful_invocation_and_failure3(self):
        cmd = [
            sys.executable, self.worker_script,
            "--model", "glm-5-3",
            "--prompt-file", self.prompt_file,
            "--receipt-dir", self.receipt_dir
        ]
        
        proc = subprocess.run(cmd, env=self.env, capture_output=True, text=True)
        # We expect exit 3 because our fake vibe exits 3
        self.assertEqual(proc.returncode, 3)
        
        # Verify receipt
        receipt_path = os.path.join(self.receipt_dir, "receipt.json")
        self.assertTrue(os.path.exists(receipt_path))
        with open(receipt_path, "r") as f:
            receipt = json.load(f)
        
        self.assertEqual(receipt["cli_version"], "2.26.1")
        self.assertEqual(receipt["requested_model"], "glm-5-3")
        self.assertEqual(receipt["wire_model"], "zai-glm-5-3")
        self.assertEqual(receipt["process_exit"], 3)
        self.assertEqual(receipt["export"]["outcome"], "success")
        self.assertEqual(receipt["usage"]["total_tokens"], 30)
        self.assertEqual(receipt["cost"], 0.05)
        
        # Ensure credentials/raw response are excluded
        self.assertNotIn("credentials", receipt)
        self.assertNotIn("raw_response", receipt)

    def test_missing_cli(self):
        env = self.env.copy()
        # Remove fake vibe from PATH
        env["PATH"] = "/usr/bin:/bin"
        
        cmd = [
            sys.executable, self.worker_script,
            "--model", "glm-5-3",
            "--prompt-file", self.prompt_file,
            "--receipt-dir", self.receipt_dir
        ]
        
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Missing or unsupported Vibe CLI", proc.stderr)

    def test_invalid_bounds(self):
        cmd = [
            sys.executable, self.worker_script,
            "--model", "glm-5-3",
            "--prompt-file", self.prompt_file,
            "--receipt-dir", self.receipt_dir,
            "--max-price", "-1"
        ]
        proc = subprocess.run(cmd, env=self.env, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("must be positive", proc.stderr)
        
    def test_unknown_model_refused(self):
        cmd = [
            sys.executable, self.worker_script,
            "--model", "unknown-model",
            "--prompt-file", self.prompt_file,
            "--receipt-dir", self.receipt_dir
        ]
        proc = subprocess.run(cmd, env=self.env, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid choice", proc.stderr.lower())

    def test_malformed_export_nonfinite_usage(self):
        # Override fake vibe to produce bad export
        with open(self.fake_vibe_bin, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("if [ \"$1\" = \"--version\" ]; then echo '2.26.1'; exit 0; fi\n")
            f.write("for i in \"$@\"; do if [ \"$i\" = \"--output-dir\" ]; then OUTDIR_FLAG=1; elif [ \"$OUTDIR_FLAG\" = \"1\" ]; then OUTDIR=$i; OUTDIR_FLAG=0; fi; done\n")
            f.write("if [ -n \"$OUTDIR\" ]; then echo '{\"schema_version\": \"1.0\", \"usage\": {\"total_tokens\": \"NaN\"}}' > \"$OUTDIR/export.json\"; fi\n")
            f.write("exit 0\n")
            
        cmd = [
            sys.executable, self.worker_script,
            "--model", "glm-5-3",
            "--prompt-file", self.prompt_file,
            "--receipt-dir", self.receipt_dir
        ]
        
        proc = subprocess.run(cmd, env=self.env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        
        receipt_path = os.path.join(self.receipt_dir, "receipt.json")
        with open(receipt_path, "r") as f:
            receipt = json.load(f)
            
        self.assertIn("export_error", receipt)

if __name__ == "__main__":
    unittest.main()
