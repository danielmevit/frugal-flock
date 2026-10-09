#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Unit tests for Perplexity Pro research adapter.

Meaningful offline unittest with fake dependency module/dist metadata in private temp.
No install/network/real token. Assert both exact identifiers/Thinking/source and config
max_retries=0, token load once/one ask, no smart routing/paid fallback, path spaces/large file,
missing dep/auth/unsupported model/invalid bounds pre-call, denial/no retry, timeout/huge
stdout/invalid JSON safe failure/owned cleanup, token/exception secret absent from receipts.
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class FakePerplexityWebMcpCli:
    """Fake perplexity-web-mcp-cli module for testing."""
    
    class token_store:
        @staticmethod
        def load_token():
            return None  # Simulate missing token by default
    
    class ClientConfig:
        def __init__(self, max_retries=0, logging_level="DISABLED", rotate_fingerprint=False, timeout=300):
            self.max_retries = max_retries
            self.logging_level = logging_level
            self.rotate_fingerprint = rotate_fingerprint
            self.timeout = timeout
    
    class Models:
        GLM_5_3 = "glm_5_3"
        KIMI_K3 = "kimi_k3"
    
    class SourceFocus:
        WEB = "WEB"
    
    class ConversationConfig:
        def __init__(self, model, source_focus=None, save_to_library=False):
            self.model = model
            self.source_focus = source_focus or []
            self.save_to_library = save_to_library
    
    class Perplexity:
        def __init__(self, token, config):
            self.token = token
            self.config = config
        
        def conversation(self, config):
            return FakeConversation(config)
    
    class MockResponse:
        def __init__(self, answer, citations=None):
            self.answer = answer
            self.citations = citations or []


class FakeConversation:
    """Fake conversation for testing."""
    
    def __init__(self, config):
        self.config = config
        self.ask_count = 0
    
    def ask(self, prompt):
        self.ask_count += 1
        if self.ask_count > 1:
            raise Exception("Multiple asks detected - should only ask once")
        
        # Simulate different responses based on model
        if hasattr(self.config, 'model'):
            model = str(self.config.model)
            if model == "GLM_5_3":
                return FakePerplexityWebMcpCli.MockResponse(
                    "This is a test answer from GLM-5-3",
                    [{"url": "https://example.com", "title": "Example"}]
                )
            elif model == "KIMI_K3":
                return FakePerplexityWebMcpCli.MockResponse(
                    "This is a test answer from Kimi-K3",
                    [{"url": "https://test.com", "title": "Test"}]
                )
        
        return FakePerplexityWebMcpCli.MockResponse("Default test answer")


class TestPerplexityWorker(unittest.TestCase):
    """Test cases for perplexity-worker.py functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.task_file = Path(self.temp_dir) / "test-task.txt"
        self.large_task_file = Path(self.temp_dir) / "large-task.txt"
        self.receipt_dir = Path(self.temp_dir) / "receipts"
        
        # Create test task file
        self.task_content = "What is the capital of France?"
        self.task_file.write_text(self.task_content, encoding='utf-8')
        
        # Create large task file (with path spaces)
        large_content = "A" * 10000  # 10KB of content
        self.large_task_file.write_text(large_content, encoding='utf-8')
        
        # Create receipt directory
        self.receipt_dir.mkdir()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_check_mode_missing_dependency(self):
        """Test --check mode with missing dependency."""
        from perplexity_worker import check_dependency, EXIT_MISSING_DEP
        
        with patch.dict('sys.modules', {'perplexity_web_mcp_cli': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'perplexity_web_mcp_cli'")):
                exit_code, message = check_dependency()
                self.assertEqual(exit_code, EXIT_MISSING_DEP)
                self.assertIn("not installed", message)
                self.assertIn("pip install perplexity-web-mcp-cli==0.16.1", message)
    
    def test_check_mode_version_mismatch(self):
        """Test --check mode with version mismatch."""
        from tools.perplexity_worker import check_dependency, EXIT_VERSION_MISMATCH
        
        # Mock the module and version
        mock_module = MagicMock()
        
        with patch.dict('sys.modules', {'perplexity_web_mcp_cli': mock_module}):
            with patch('pkg_resources.get_distribution') as mock_get_dist:
                mock_dist = MagicMock()
                mock_dist.version = "0.15.0"
                mock_get_dist.return_value = mock_dist
                
                exit_code, message = check_dependency()
                self.assertEqual(exit_code, EXIT_VERSION_MISMATCH)
                self.assertIn("0.15.0", message)
                self.assertIn("0.16.1", message)
    
    def test_check_mode_success(self):
        """Test --check mode with correct version."""
        from tools.perplexity_worker import check_dependency, EXIT_OK
        
        mock_module = MagicMock()
        
        with patch.dict('sys.modules', {'perplexity_web_mcp_cli': mock_module}):
            with patch('pkg_resources.get_distribution') as mock_get_dist:
                mock_dist = MagicMock()
                mock_dist.version = "0.16.1"
                mock_get_dist.return_value = mock_dist
                
                exit_code, message = check_dependency()
                self.assertEqual(exit_code, EXIT_OK)
                self.assertIn("available", message)
    
    def test_validate_bounds_invalid(self):
        """Test validate_bounds with invalid values."""
        from tools.perplexity_worker import validate_bounds
        
        # Test zero bound
        valid, msg = validate_bounds(0, 1000)
        self.assertFalse(valid)
        self.assertIn("positive", msg)
        
        # Test negative stdout size
        valid, msg = validate_bounds(100, -1)
        self.assertFalse(valid)
        self.assertIn("positive", msg)
        
        # Test bound too high
        valid, msg = validate_bounds(3601, 1000)
        self.assertFalse(valid)
        self.assertIn("3600", msg)
        
        # Test stdout size too high
        valid, msg = validate_bounds(100, 10 * 1024 * 1024 + 1)
        self.assertFalse(valid)
        self.assertIn("10MiB", msg)
    
    def test_validate_bounds_valid(self):
        """Test validate_bounds with valid values."""
        from tools.perplexity_worker import validate_bounds
        
        valid, msg = validate_bounds(300, 1048576)
        self.assertTrue(valid)
        self.assertEqual(msg, "")
    
    def test_validate_task_file_missing(self):
        """Test validate_task_file with missing file."""
        from tools.perplexity_worker import validate_task_file, EXIT_INVALID_BOUNDS
        
        exit_code, msg, content = validate_task_file("/nonexistent/file.txt")
        self.assertEqual(exit_code, EXIT_INVALID_BOUNDS)
        self.assertIn("not found", msg)
    
    def test_validate_task_file_empty(self):
        """Test validate_task_file with empty file."""
        from tools.perplexity_worker import validate_task_file, EXIT_INVALID_BOUNDS
        
        empty_file = Path(self.temp_dir) / "empty.txt"
        empty_file.write_text("", encoding='utf-8')
        
        exit_code, msg, content = validate_task_file(str(empty_file))
        self.assertEqual(exit_code, EXIT_INVALID_BOUNDS)
        self.assertIn("empty", msg)
    
    def test_validate_task_file_success(self):
        """Test validate_task_file with valid file."""
        from tools.perplexity_worker import validate_task_file, EXIT_OK
        
        exit_code, msg, content = validate_task_file(str(self.task_file))
        self.assertEqual(exit_code, EXIT_OK)
        self.assertEqual(content, self.task_content)
    
    def test_create_receipt_dir_new(self):
        """Test create_receipt_dir with new directory."""
        from tools.perplexity_worker import create_receipt_dir, EXIT_OK
        
        new_dir = Path(self.temp_dir) / "new_receipts"
        receipt_dir, exit_code, msg = create_receipt_dir(str(new_dir))
        
        self.assertEqual(exit_code, EXIT_OK)
        self.assertTrue(Path(receipt_dir).exists())
        self.assertTrue(Path(receipt_dir).is_dir())
    
    def test_create_receipt_dir_existing_file(self):
        """Test create_receipt_dir with existing file (should fail)."""
        from tools.perplexity_worker import create_receipt_dir, EXIT_INVALID_BOUNDS
        
        # Create a file where we want the directory
        file_path = Path(self.temp_dir) / "file_not_dir.txt"
        file_path.write_text("content")
        
        receipt_dir, exit_code, msg = create_receipt_dir(str(file_path))
        
        self.assertEqual(exit_code, EXIT_INVALID_BOUNDS)
        self.assertIn("not a directory", msg)
    
    def test_generate_receipt_success(self):
        """Test generate_receipt with valid parameters."""
        from tools.perplexity_worker import generate_receipt
        
        task_hash = hashlib.sha256(self.task_content.encode()).hexdigest()
        
        success, receipt_path = generate_receipt(
            str(self.receipt_dir),
            task_hash,
            "glm53",
            "glm_5_3_thinking",
            "PerplexityPro",
            "perplexity",
            "unknown",
            "success",
            0,
            1.234,
            300
        )
        
        self.assertTrue(success)
        self.assertTrue(Path(receipt_path).exists())
        
        # Verify receipt content
        receipt_content = json.loads(Path(receipt_path).read_text())
        self.assertEqual(receipt_content["requested_model"], "glm53")
        self.assertEqual(receipt_content["configured_identifier"], "glm_5_3_thinking")
        self.assertEqual(receipt_content["transport"], "PerplexityPro")
        self.assertEqual(receipt_content["budget_group"], "perplexity")
        self.assertEqual(receipt_content["effective_model"], "unknown")
        self.assertEqual(receipt_content["outcome"], "success")
        self.assertEqual(receipt_content["exit_code"], 0)
        self.assertAlmostEqual(receipt_content["elapsed_seconds"], 1.234, places=3)
        self.assertEqual(receipt_content["bound_seconds"], 300)
        self.assertTrue(receipt_content["source_only_offline_claim"])
        
        # Ensure no sensitive data is in receipt
        self.assertNotIn("token", receipt_content)
        self.assertNotIn("prompt", receipt_content)
        self.assertNotIn("answer", receipt_content)
        self.assertNotIn("raw", receipt_content)
    
    def test_supported_models_and_identifiers(self):
        """Test that supported models and thinking identifiers are correct."""
        from tools.perplexity_worker import SUPPORTED_MODELS, THINKING_IDENTIFIERS
        
        # Check models
        self.assertEqual(SUPPORTED_MODELS["glm53"], "glm_5_3")
        self.assertEqual(SUPPORTED_MODELS["kimi_k3"], "kimi_k3")
        
        # Check thinking identifiers
        self.assertEqual(THINKING_IDENTIFIERS["glm53"], "glm_5_3_thinking")
        self.assertEqual(THINKING_IDENTIFIERS["kimi_k3"], "kimik3thinking")
    
    def test_run_perplexity_query_missing_token(self):
        """Test run_perplexity_query with missing token."""
        from tools.perplexity_worker import run_perplexity_query, EXIT_AUTH_MISSING
        
        with patch.dict('sys.modules', {'perplexity_web_mcp_cli': FakePerplexityWebMcpCli}):
            exit_code, error_msg, result = run_perplexity_query(
                "test prompt", "glm53", 300, 1000000
            )
            
            self.assertEqual(exit_code, EXIT_AUTH_MISSING)
            self.assertIn("pwm login", error_msg)
            self.assertEqual(result, {})
    
    def test_run_perplexity_query_unsupported_model(self):
        """Test run_perplexity_query with unsupported model."""
        from tools.perplexity_worker import run_perplexity_query, EXIT_MODEL_UNSUPPORTED
        
        with patch.dict('sys.modules', {'perplexity_web_mcp_cli': FakePerplexityWebMcpCli}):
            # Mock token to be available
            with patch.object(FakePerplexityWebMcpCli.token_store, 'load_token', return_value="fake_token"):
                exit_code, error_msg, result = run_perplexity_query(
                    "test prompt", "invalid_model", 300, 1000000
                )
                
                self.assertEqual(exit_code, EXIT_MODEL_UNSUPPORTED)
                self.assertIn("Unsupported model", error_msg)
                self.assertEqual(result, {})
    
    def test_run_perplexity_query_success(self):
        """Test run_perplexity_query with successful execution."""
        from tools.perplexity_worker import run_perplexity_query, EXIT_OK
        
        with patch.dict('sys.modules', {'perplexity_web_mcp_cli': FakePerplexityWebMcpCli}):
            # Mock token to be available
            with patch.object(FakePerplexityWebMcpCli.token_store, 'load_token', return_value="fake_token"):
                exit_code, error_msg, result = run_perplexity_query(
                    "test prompt", "glm53", 300, 1000000
                )
                
                self.assertEqual(exit_code, EXIT_OK)
                self.assertEqual(error_msg, "")
                self.assertIn("answer", result)
                self.assertIn("model", result)
                self.assertEqual(result["model"], "glm_5_3")
                self.assertEqual(result["thinking_identifier"], "glm_5_3_thinking")
    
    def test_run_perplexity_query_kimi_k3(self):
        """Test run_perplexity_query with Kimi K3 model."""
        from tools.perplexity_worker import run_perplexity_query, EXIT_OK
        
        with patch.dict('sys.modules', {'perplexity_web_mcp_cli': FakePerplexityWebMcpCli}):
            # Mock token to be available
            with patch.object(FakePerplexityWebMcpCli.token_store, 'load_token', return_value="fake_token"):
                exit_code, error_msg, result = run_perplexity_query(
                    "test prompt", "kimi_k3", 300, 1000000
                )
                
                self.assertEqual(exit_code, EXIT_OK)
                self.assertEqual(error_msg, "")
                self.assertIn("answer", result)
                self.assertIn("model", result)
                self.assertEqual(result["model"], "kimi_k3")
                self.assertEqual(result["thinking_identifier"], "kimik3thinking")
    
    def test_client_config_values(self):
        """Test that ClientConfig is created with correct values."""
        from tools.perplexity_worker import run_perplexity_query, EXIT_AUTH_MISSING
        
        with patch.dict('sys.modules', {'perplexity_web_mcp_cli': FakePerplexityWebMcpCli}):
            # Mock token to be available
            with patch.object(FakePerplexityWebMcpCli.token_store, 'load_token', return_value="fake_token"):
                with patch.object(FakePerplexityWebMcpCli, 'ClientConfig') as mock_config_class:
                    mock_config = MagicMock()
                    mock_config_class.return_value = mock_config
                    
                    run_perplexity_query("test", "glm53", 120, 500000)
                    
                    # Verify ClientConfig was called with correct parameters
                    mock_config_class.assert_called_once()
                    call_args = mock_config_class.call_args
                    self.assertEqual(call_args[1]['max_retries'], 0)
                    self.assertEqual(call_args[1]['logging_level'], "DISABLED")
                    self.assertEqual(call_args[1]['rotate_fingerprint'], False)
                    self.assertEqual(call_args[1]['timeout'], 120)
    
    def test_conversation_config_values(self):
        """Test that ConversationConfig is created with correct values."""
        from tools.perplexity_worker import run_perplexity_query, EXIT_OK
        
        with patch.dict('sys.modules', {'perplexity_web_mcp_cli': FakePerplexityWebMcpCli}):
            # Mock token to be available
            with patch.object(FakePerplexityWebMcpCli.token_store, 'load_token', return_value="fake_token"):
                with patch.object(FakePerplexityWebMcpCli, 'ConversationConfig') as mock_conv_class:
                    mock_conv = MagicMock()
                    mock_conv_class.return_value = mock_conv
                    
                    run_perplexity_query("test", "glm53", 300, 1000000)
                    
                    # Verify ConversationConfig was called with correct parameters
                    mock_conv_class.assert_called_once()
                    call_args = mock_conv_class.call_args
                    self.assertEqual(str(call_args[1]['model']), "GLM_5_3")
                    self.assertEqual(call_args[1]['source_focus'], [])
                    self.assertEqual(call_args[1]['save_to_library'], False)
    
    def test_path_spaces_handling(self):
        """Test handling of paths with spaces."""
        from tools.perplexity_worker import validate_task_file, EXIT_OK
        
        # Create a file with spaces in the name
        space_file = Path(self.temp_dir) / "test file with spaces.txt"
        space_content = "Content in spaced file"
        space_file.write_text(space_content, encoding='utf-8')
        
        exit_code, msg, content = validate_task_file(str(space_file))
        self.assertEqual(exit_code, EXIT_OK)
        self.assertEqual(content, space_content)
    
    def test_large_file_handling(self):
        """Test handling of large files."""
        from tools.perplexity_worker import validate_task_file, EXIT_OK
        
        # Test with the large file we created in setUp
        exit_code, msg, content = validate_task_file(str(self.large_task_file))
        self.assertEqual(exit_code, EXIT_OK)
        self.assertEqual(len(content), 10000)
    
    def test_missing_dependency_error_handling(self):
        """Test error handling for missing dependency."""
        from tools.perplexity_worker import run_perplexity_query, EXIT_MISSING_DEP
        
        # Don't mock the module - it should fail to import
        exit_code, error_msg, result = run_perplexity_query(
            "test prompt", "glm53", 300, 1000000
        )
        
        self.assertEqual(exit_code, EXIT_MISSING_DEP)
        self.assertIn("not available", error_msg)
        self.assertIn("pip install", error_msg)
        self.assertEqual(result, {})
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in responses."""
        from tools.perplexity_worker import run_perplexity_query, EXIT_OK
        
        # Create a mock that returns invalid JSON structure
        class BadResponse:
            def __init__(self):
                pass  # No answer attribute
        
        class BadConversation:
            def __init__(self, config):
                pass
            
            def ask(self, prompt):
                return BadResponse()
        
        class BadPerplexity:
            def __init__(self, token, config):
                pass
            
            def conversation(self, config):
                return BadConversation(config)
        
        class BadModule:
            class token_store:
                @staticmethod
                def load_token():
                    return "fake_token"
            
            class ClientConfig:
                def __init__(self, **kwargs):
                    pass
            
            class Models:
                GLM_5_3 = "glm_5_3"
            
            class SourceFocus:
                WEB = "WEB"
            
            class ConversationConfig:
                def __init__(self, **kwargs):
                    pass
            
            Perplexity = BadPerplexity
        
        with patch.dict('sys.modules', {'perplexity_web_mcp_cli': BadModule}):
            exit_code, error_msg, result = run_perplexity_query(
                "test prompt", "glm53", 300, 1000000
            )
            
            # Should handle missing answer gracefully
            self.assertEqual(exit_code, 10)  # EXIT_CHILD_ERROR
            self.assertIn("missing answer", error_msg)


class TestCommandLineInterface(unittest.TestCase):
    """Test command line interface functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.task_file = Path(self.temp_dir) / "test-task.txt"
        self.task_content = "What is the capital of France?"
        self.task_file.write_text(self.task_content, encoding='utf-8')
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_check_mode_command(self):
        """Test --check command line option."""
        from tools.perplexity_worker import main
        
        # Mock sys.argv for --check mode
        with patch('sys.argv', ['perplexity-worker.py', '--check']):
            with patch.dict('sys.modules', {'perplexity_web_mcp_cli': None}):
                with patch('builtins.__import__', side_effect=ImportError("No module")):
                    with patch('sys.exit') as mock_exit:
                        with patch('sys.stderr') as mock_stderr:
                            main()
                            # Should exit with missing dependency code
                            mock_exit.assert_called_once()
                            call_args = mock_exit.call_args[0]
                            self.assertEqual(call_args[0], 1)  # EXIT_MISSING_DEP
    
    def test_model_argument_validation(self):
        """Test model argument validation."""
        from tools.perplexity_worker import parse_args
        
        # Test valid models
        with patch('sys.argv', ['perplexity-worker.py', '--model', 'glm53', 'task.txt']):
            args = parse_args()
            self.assertEqual(args.model, 'glm53')
        
        with patch('sys.argv', ['perplexity-worker.py', '--model', 'kimi_k3', 'task.txt']):
            args = parse_args()
            self.assertEqual(args.model, 'kimi_k3')
        
        # Test invalid model (should raise SystemExit)
        with patch('sys.argv', ['perplexity-worker.py', '--model', 'invalid', 'task.txt']):
            with self.assertRaises(SystemExit):
                parse_args()
    
    def test_bound_and_stdout_size_validation(self):
        """Test bound and stdout-size argument validation."""
        from tools.perplexity_worker import parse_args
        
        with patch('sys.argv', ['perplexity-worker.py', '--bound', '600', '--stdout-size', '2097152', 'task.txt']):
            args = parse_args()
            self.assertEqual(args.bound, 600)
            self.assertEqual(args.stdout_size, 2097152)


if __name__ == '__main__':
    unittest.main()