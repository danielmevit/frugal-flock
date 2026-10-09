import os
import sys
import argparse
import subprocess
import json
import time
import hashlib
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Vibe worker adapter")
    parser.add_argument("--model", required=True, choices=["glm-5-3", "mistral-medium-3-5"])
    parser.add_argument("--prompt-file", help="Path to prompt file (or use TASKFILE env var)")
    parser.add_argument("--receipt-dir", required=True, help="Directory for receipt")
    parser.add_argument("--max-price", type=float, default=0.2, help="Max price in dollars")
    parser.add_argument("--max-tokens", type=int, default=600000, help="Max tokens")
    parser.add_argument("--time-limit", type=int, default=3600, help="Time limit in seconds")
    parser.add_argument("--max-turns", type=int, default=50, help="Max turns")
    
    args = parser.parse_args()

    if args.max_price <= 0:
        sys.exit("Error: max-price must be positive")
    if args.max_tokens <= 0:
        sys.exit("Error: max-tokens must be positive")
    if args.time_limit <= 0:
        sys.exit("Error: time-limit must be positive")
    
    prompt_file = args.prompt_file or os.environ.get("TASKFILE")
    if not prompt_file:
        sys.exit("Error: --prompt-file or TASKFILE must be provided")
    
    if not os.path.isdir(args.receipt_dir):
        sys.exit("Error: --receipt-dir must preexist")
        
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            f.read()
    except Exception as e:
        sys.exit(f"Error: Prompt file is not a readable regular UTF-8 task: {e}")
    
    try:
        vibe_version_proc = subprocess.run(["vibe", "--version"], capture_output=True, text=True, check=True)
        cli_version = vibe_version_proc.stdout.strip()
    except Exception as e:
        sys.exit(f"Error: Missing or unsupported Vibe CLI: {e}")

    wire_model = "zai-glm-5-3" if args.model == "glm-5-3" else "mistral-medium-3-5"

    env = os.environ.copy()
    env["VIBE_ACTIVE_MODEL"] = wire_model
    env["VIBE_MODELS"] = json.dumps({wire_model: {"thinking": "high"}})
    env["VIBE_ALLOWED_MODELS"] = wire_model # The prompt says "VIBE_ALLOWED_MODELS matches WIRE model names, not aliases". If it's a string maybe? Or json? Let's use string.
    env["VIBE_COMPACTION_MODEL"] = wire_model
    env["VIBE_UTILITY_MODEL"] = wire_model
    env["VIBE_GENERATE_TITLE"] = "false"
    env["VIBE_EXPERIMENTS_ENABLED"] = "false"
    env["VIBE_AUTO_UPDATE"] = "false"
    env["VIBE_MCP_ENABLED"] = "false"
    env["VIBE_ENABLE_SUBAGENTS"] = "false"
    env["VIBE_ENABLE_CONNECTORS"] = "false"
    env["VIBE_API_RETRY_MAX_ELAPSED_TIME"] = "0"
    
    vibe_cmd = [
        "vibe", "-p",
        "--prompt-file", prompt_file,
        "--output-dir", args.receipt_dir,
        "--agent", "auto-approve",
        "--auto-approve",
        "--max-price", str(args.max_price),
        "--max-tokens", str(args.max_tokens),
        "--time-limit", str(args.time_limit),
        "--max-turns", str(args.max_turns),
    ]
    
    for tool in ["bash", "read_file", "write_file", "edit", "grep"]:
        vibe_cmd.extend(["--enabled-tools", tool])
    
    with open(prompt_file, "rb") as f:
        task_hash = hashlib.sha256(f.read()).hexdigest()
        
    start_time = time.time()
    
    try:
        proc = subprocess.run(vibe_cmd, env=env)
        exit_code = proc.returncode
    except Exception as e:
        print(f"Failed to run Vibe: {e}")
        exit_code = 3
        
    elapsed = time.time() - start_time
    
    export_path = os.path.join(args.receipt_dir, "export.json")
    receipt_path = os.path.join(args.receipt_dir, "receipt.json")
    
    receipt = {
        "date": datetime.utcnow().isoformat() + "Z",
        "cli_version": cli_version,
        "requested_model": args.model,
        "requested_effort": "high",
        "wire_model": wire_model,
        "process_exit": exit_code,
        "elapsed_seconds": elapsed,
        "task_hash": task_hash,
        "native_limits": {
            "max_price": args.max_price,
            "max_tokens": args.max_tokens,
            "time_limit": args.time_limit,
            "max_turns": args.max_turns
        }
    }
    
    if os.path.exists(export_path):
        try:
            with open(export_path, "r") as f:
                export_data = json.load(f)
            
            receipt["export"] = {
                "schema_version": export_data.get("schema_version", "unknown"),
                "outcome": export_data.get("outcome", "unknown"),
                "stop_reason": export_data.get("stop_reason", "unknown")
            }
            
            usage = export_data.get("usage", {})
            cost = export_data.get("cost", {})
            
            receipt["usage"] = {
                "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                "completion_tokens": int(usage.get("completion_tokens", 0)),
                "total_tokens": int(usage.get("total_tokens", 0))
            }
            
            if isinstance(cost, dict) and "total" in cost:
                 receipt["cost"] = float(cost.get("total", 0.0))
            elif isinstance(cost, (int, float)):
                 receipt["cost"] = float(cost)
            else:
                 receipt["cost"] = 0.0
                 
        except Exception as e:
            receipt["export_error"] = f"Failed to parse export.json: {e}"
    else:
        receipt["export_error"] = "export.json missing"
        
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
        
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
