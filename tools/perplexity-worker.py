#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Perplexity Pro research adapter and inspected connector comparison.

Stdlib adapter/orchestrator for Perplexity Pro research functionality.
Uses perplexity-web-mcp-cli 0.16.1 as optional external dependency.

Usage:
    python3 tools/perplexity-worker.py [--check] [--model glm53|kimi_k3] [--receipt-dir DIR] [--bound SECONDS] [--stdout-size BYTES] [TASK_FILE]

Options:
    --check              Only check dependency metadata/version/import availability
    --model              Model to use: glm53 or kimi_k3 (default: glm53)
    --receipt-dir DIR    Directory for receipt files (default: none)
    --bound SECONDS      Timeout bound in seconds (default: 300)
    --stdout-size BYTES  Maximum stdout size in bytes (default: 1048576 = 1MiB)
    TASK_FILE            Path to task file (required for actual queries)

Environment:
    The perplexity-web-mcp-cli package must be manually installed by the owner
    in the interpreter used. This script will not auto-install dependencies.

Security:
    - No network calls during --check
    - No actual API usage without explicit owner install/signin
    - No token, prompt, raw answer or raw config copied to receipts
    - Safe error handling with clear states and nonzero exit codes
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Constants
REQUIRED_VERSION = "0.16.1"
SUPPORTED_MODELS = {"glm53": "glm_5_3", "kimi_k3": "kimi_k3"}
THINKING_IDENTIFIERS = {"glm53": "glm_5_3_thinking", "kimi_k3": "kimik3thinking"}
DEFAULT_BOUND = 300  # seconds
DEFAULT_STDOUT_SIZE = 1048576  # 1MiB

# Exit codes
EXIT_OK = 0
EXIT_MISSING_DEP = 1
EXIT_VERSION_MISMATCH = 2
EXIT_IMPORT_ERROR = 3
EXIT_AUTH_MISSING = 4
EXIT_MODEL_UNSUPPORTED = 5
EXIT_TIMEOUT = 6
EXIT_STDOUT_OVERFLOW = 7
EXIT_INVALID_JSON = 8
EXIT_INVALID_BOUNDS = 9
EXIT_CHILD_ERROR = 10


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Perplexity Pro research adapter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment:
  The perplexity-web-mcp-cli package must be manually installed by the owner.
  Use: pip install perplexity-web-mcp-cli==0.16.1
  Then: pwm login (follow email OTP flow)
        """
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check dependency metadata/version/import availability"
    )
    parser.add_argument(
        "--model",
        choices=["glm53", "kimi_k3"],
        default="glm53",
        help="Model to use: glm53 or kimi_k3"
    )
    parser.add_argument(
        "--receipt-dir",
        type=str,
        default=None,
        help="Directory for receipt files"
    )
    parser.add_argument(
        "--bound",
        type=int,
        default=DEFAULT_BOUND,
        help=f"Timeout bound in seconds (default: {DEFAULT_BOUND})"
    )
    parser.add_argument(
        "--stdout-size",
        type=int,
        default=DEFAULT_STDOUT_SIZE,
        help=f"Maximum stdout size in bytes (default: {DEFAULT_STDOUT_SIZE})"
    )
    parser.add_argument(
        "task_file",
        type=str,
        nargs="?",
        help="Path to task file (required for actual queries)"
    )
    
    return parser.parse_args()


def validate_bounds(bound: int, stdout_size: int) -> Tuple[bool, str]:
    """Validate that bounds are finite and reasonable."""
    if bound <= 0:
        return False, "bound must be positive"
    if stdout_size <= 0:
        return False, "stdout-size must be positive"
    if bound > 3600:  # 1 hour max
        return False, "bound exceeds maximum of 3600 seconds"
    if stdout_size > 10 * 1024 * 1024:  # 10MiB max
        return False, "stdout-size exceeds maximum of 10MiB"
    return True, ""


def check_dependency() -> Tuple[int, str]:
    """Check if perplexity-web-mcp-cli is available and at the right version."""
    try:
        # Try to import the package
        import perplexity_web_mcp_cli
        import pkg_resources
        
        # Check version
        try:
            installed_version = pkg_resources.get_distribution("perplexity-web-mcp-cli").version
            if installed_version != REQUIRED_VERSION:
                return (EXIT_VERSION_MISMATCH, 
                       f"perplexity-web-mcp-cli version {installed_version} found, "
                       f"required: {REQUIRED_VERSION}")
        except Exception:
            # If we can't get version via pkg_resources, try importlib.metadata
            try:
                from importlib import metadata
                installed_version = metadata.version("perplexity-web-mcp-cli")
                if installed_version != REQUIRED_VERSION:
                    return (EXIT_VERSION_MISMATCH,
                           f"perplexity-web-mcp-cli version {installed_version} found, "
                           f"required: {REQUIRED_VERSION}")
            except Exception as e:
                return (EXIT_VERSION_MISMATCH, 
                       f"Cannot determine perplexity-web-mcp-cli version: {e}")
        
        return EXIT_OK, "perplexity-web-mcp-cli >= 0.16.1 available"
        
    except ImportError:
        return (EXIT_MISSING_DEP, 
               "perplexity-web-mcp-cli not installed. "
               "Install with: pip install perplexity-web-mcp-cli==0.16.1")
    except Exception as e:
        return (EXIT_IMPORT_ERROR, f"Error checking perplexity-web-mcp-cli: {e}")


def validate_task_file(task_file: str) -> Tuple[int, str, str]:
    """Validate task file exists and is readable."""
    if not task_file:
        return (EXIT_INVALID_BOUNDS, "Task file is required for query mode", "")
    
    try:
        path = Path(task_file)
        if not path.exists():
            return (EXIT_INVALID_BOUNDS, f"Task file not found: {task_file}", "")
        if not path.is_file():
            return (EXIT_INVALID_BOUNDS, f"Task file is not a regular file: {task_file}", "")
        if path.stat().st_size == 0:
            return (EXIT_INVALID_BOUNDS, f"Task file is empty: {task_file}", "")
        
        # Check it's valid UTF-8
        content = path.read_text(encoding='utf-8')
        return EXIT_OK, "", content
        
    except Exception as e:
        return (EXIT_INVALID_BOUNDS, f"Error reading task file: {e}", "")


def create_receipt_dir(receipt_dir: Optional[str]) -> Tuple[Optional[str], int, str]:
    """Create or validate receipt directory."""
    if receipt_dir is None:
        return None, EXIT_OK, ""
    
    try:
        path = Path(receipt_dir)
        if path.exists():
            if not path.is_dir():
                return None, EXIT_INVALID_BOUNDS, f"Receipt path exists but is not a directory: {receipt_dir}"
        else:
            path.mkdir(parents=True, exist_ok=True)
        return str(path), EXIT_OK, ""
    except Exception as e:
        return None, EXIT_INVALID_BOUNDS, f"Error creating receipt directory: {e}"


def generate_receipt(
    receipt_dir: str,
    task_hash: str,
    requested_model: str,
    configured_identifier: str,
    transport: str,
    budget_group: str,
    effective_model: str,
    outcome: str,
    exit_code: int,
    elapsed: float,
    bound: int,
    source_only: bool = True
) -> Tuple[bool, str]:
    """Generate a receipt file with sanitized metadata."""
    try:
        from datetime import datetime
        import hashlib
        
        # Generate filename from task hash and date
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{date_str}-{task_hash[:12]}-perplexity-receipt.json"
        receipt_path = Path(receipt_dir) / filename
        
        # Create receipt content (no tokens, prompts, raw answers, or raw configs)
        receipt = {
            "source": "task_hash" if source_only else "live",
            "date": datetime.now().isoformat(),
            "requested_model": requested_model,
            "configured_identifier": configured_identifier,
            "transport": transport,
            "budget_group": budget_group,
            "effective_model": effective_model,
            "outcome": outcome,
            "exit_code": exit_code,
            "elapsed_seconds": round(elapsed, 3),
            "bound_seconds": bound,
            "source_only_offline_claim": source_only
        }
        
        # Write receipt
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        return True, str(receipt_path)
        
    except Exception as e:
        return False, f"Error generating receipt: {e}"


def run_perplexity_query(
    prompt: str,
    model_key: str,
    bound: int,
    stdout_size: int
) -> Tuple[int, str, Dict[str, Any]]:
    """Run a Perplexity query using the direct library route."""
    try:
        # Import the library - this will fail if not installed
        from perplexity_web_mcp_cli import token_store, ClientConfig, Perplexity, ConversationConfig, Models, SourceFocus
        
        # Load token once (missing => manual pwm login instruction)
        token = token_store.load_token()
        if token is None:
            return (EXIT_AUTH_MISSING, 
                   "Perplexity token not found. Run: pwm login (follow email OTP flow)",
                   {})
        
        # Get model and thinking identifier
        model_name = SUPPORTED_MODELS.get(model_key)
        if model_name is None:
            return (EXIT_MODEL_UNSUPPORTED, 
                   f"Unsupported model: {model_key}. Supported: {', '.join(SUPPORTED_MODELS.keys())}",
                   {})
        
        thinking_identifier = THINKING_IDENTIFIERS.get(model_key, "unknown")
        
        # Configure client with retries disabled
        config = ClientConfig(
            max_retries=0,
            logging_level="DISABLED",
            rotate_fingerprint=False,
            timeout=bound
        )
        
        # Create Perplexity client
        client = Perplexity(token=token, config=config)
        
        # Configure conversation - no smart routing, no fallback
        conversation_config = ConversationConfig(
            model=getattr(Models, model_name.upper()),
            source_focus=[],  # [] for none, [SourceFocus.WEB] for web
            save_to_library=False
        )
        
        # Create conversation and ask
        conversation = client.conversation(conversation_config)
        
        # Execute with timeout
        start_time = time.time()
        try:
            response = conversation.ask(prompt)
            elapsed = time.time() - start_time
            
            # Validate response shape
            if not hasattr(response, 'answer') or response.answer is None:
                return (EXIT_CHILD_ERROR, "Invalid response: missing answer", {})
            
            # Check for citations if available
            citations = []
            if hasattr(response, 'citations') and response.citations:
                citations = response.citations
            
            # Create sanitized result
            result = {
                "answer": response.answer,
                "citations": citations,
                "model": model_name,
                "thinking_identifier": thinking_identifier,
                "elapsed": elapsed
            }
            
            return EXIT_OK, "", result
            
        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed >= bound:
                return EXIT_TIMEOUT, f"Query timed out after {bound} seconds", {}
            else:
                # Map various errors to safe states
                error_str = str(e).lower()
                if "auth" in error_str or "token" in error_str:
                    return EXIT_AUTH_MISSING, f"Authentication error: {e}", {}
                elif "rate" in error_str or "limit" in error_str:
                    return EXIT_CHILD_ERROR, f"Rate limit error: {e}", {}
                elif "model" in error_str or "unsupported" in error_str:
                    return EXIT_MODEL_UNSUPPORTED, f"Model error: {e}", {}
                else:
                    return EXIT_CHILD_ERROR, f"Query error: {e}", {}
                    
    except ImportError as e:
        return (EXIT_MISSING_DEP, 
               f"perplexity-web-mcp-cli not available: {e}. "
               "Install with: pip install perplexity-web-mcp-cli==0.16.1",
               {})
    except Exception as e:
        return (EXIT_CHILD_ERROR, f"Unexpected error: {e}", {})


def execute_child_process(
    script_path: str,
    args: List[str],
    bound: int,
    stdout_size: int,
    env: Optional[Dict[str, str]] = None
) -> Tuple[int, str, str]:
    """Execute a child process with bounds and capture output."""
    try:
        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        # Start process
        cmd = [sys.executable, "-B", script_path] + args
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            env=process_env,
            preexec_fn=os.setsid if os.name == 'posix' else None
        )
        
        # Wait with timeout
        try:
            stdout, stderr = process.communicate(timeout=bound)
        except subprocess.TimeoutExpired:
            # Kill the process group
            if os.name == 'posix':
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except OSError:
                    pass
                try:
                    process.kill()
                except OSError:
                    pass
            else:
                process.kill()
            
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
            
            return EXIT_TIMEOUT, f"Child process timed out after {bound} seconds", ""
        
        # Check stdout size
        if stdout and len(stdout.encode('utf-8')) > stdout_size:
            return EXIT_STDOUT_OVERFLOW, f"Stdout exceeds {stdout_size} bytes", stdout[:stdout_size]
        
        # Check return code
        if process.returncode != 0:
            return process.returncode, f"Child process failed with exit code {process.returncode}", stdout
        
        return EXIT_OK, "", stdout
        
    except Exception as e:
        return EXIT_CHILD_ERROR, f"Error executing child process: {e}", ""


def main():
    """Main entry point."""
    args = parse_args()
    
    # Validate bounds first
    bounds_ok, bounds_msg = validate_bounds(args.bound, args.stdout_size)
    if not bounds_ok:
        print(f"Error: {bounds_msg}", file=sys.stderr)
        sys.exit(EXIT_INVALID_BOUNDS)
    
    # Check mode
    if args.check:
        # Only check dependency
        exit_code, message = check_dependency()
        if exit_code == EXIT_OK:
            print(f"OK: {message}")
            print("Auth status: unknown (not checked)")
            print("Effective model: unknown")
            print("Remaining capacity: unknown")
        else:
            print(f"ERROR: {message}", file=sys.stderr)
        sys.exit(exit_code)
    
    # Query mode - need task file
    if not args.task_file:
        print("Error: task_file is required for query mode", file=sys.stderr)
        sys.exit(EXIT_INVALID_BOUNDS)
    
    # Validate task file
    task_exit, task_msg, task_content = validate_task_file(args.task_file)
    if task_exit != EXIT_OK:
        print(f"Error: {task_msg}", file=sys.stderr)
        sys.exit(task_exit)
    
    # Create receipt directory if specified
    receipt_dir, dir_exit, dir_msg = create_receipt_dir(args.receipt_dir)
    if dir_exit != EXIT_OK:
        print(f"Error: {dir_msg}", file=sys.stderr)
        sys.exit(dir_exit)
    
    # Check dependency first
    dep_exit, dep_msg = check_dependency()
    if dep_exit != EXIT_OK:
        print(f"Error: {dep_msg}", file=sys.stderr)
        if receipt_dir:
            task_hash = hashlib.sha256(task_content.encode()).hexdigest()
            generate_receipt(
                receipt_dir, task_hash, args.model, 
                THINKING_IDENTIFIERS.get(args.model, "unknown"),
                "PerplexityPro", "perplexity", "unknown",
                "dependency_missing", dep_exit, 0, args.bound
            )
        sys.exit(dep_exit)
    
    # Calculate task hash for receipt
    import hashlib
    task_hash = hashlib.sha256(task_content.encode()).hexdigest()
    
    # Execute the query
    start_time = time.time()
    exit_code, error_msg, result = run_perplexity_query(
        task_content, args.model, args.bound, args.stdout_size
    )
    elapsed = time.time() - start_time
    
    if exit_code != EXIT_OK:
        print(f"Error: {error_msg}", file=sys.stderr)
        if receipt_dir:
            generate_receipt(
                receipt_dir, task_hash, args.model,
                THINKING_IDENTIFIERS.get(args.model, "unknown"),
                "PerplexityPro", "perplexity", "unknown",
                error_msg.split(':')[0] if error_msg else "error",
                exit_code, elapsed, args.bound
            )
        sys.exit(exit_code)
    
    # Output the result
    print(json.dumps({
        "answer": result.get("answer", ""),
        "citations": result.get("citations", []),
        "model": result.get("model", "unknown"),
        "thinking_identifier": result.get("thinking_identifier", "unknown"),
        "elapsed": result.get("elapsed", 0)
    }, indent=2))
    
    # Generate receipt if requested
    if receipt_dir:
        success, receipt_path = generate_receipt(
            receipt_dir, task_hash, args.model,
            result.get("thinking_identifier", "unknown"),
            "PerplexityPro", "perplexity", "unknown",
            "success", exit_code, elapsed, args.bound
        )
        if not success:
            print(f"Warning: {receipt_path}", file=sys.stderr)
    
    sys.exit(EXIT_OK)


if __name__ == '__main__':
    main()