# Perplexity Web Integration

This document describes the Perplexity Pro research adapter integration for Unio.
The adapter uses the `perplexity-web-mcp-cli` package as an optional external dependency.

## Overview

The Perplexity Pro research adapter provides a stdlib adapter/orchestrator that enables
research functionality using Perplexity's advanced AI models. This integration is designed
to be:

- **Optional**: The dependency must be manually installed by the repository owner
- **Safe**: No automatic network calls, no token exposure in logs or receipts
- **Bounded**: All operations have configurable timeouts and output size limits
- **Transparent**: Clear error handling and receipt generation

## Installation

### Manual Installation (Required)

The `perplexity-web-mcp-cli` package must be manually installed in the Python interpreter
used by Unio. The adapter requires version **0.16.1** exactly.

```bash
# Create and activate a virtual environment (recommended)
python3 -m venv perplexity-venv
source perplexity-venv/bin/activate  # On Linux/Mac
# or: perplexity-venv\Scripts\activate  # On Windows

# Install the required version
pip install perplexity-web-mcp-cli==0.16.1
```

### Authentication

After installation, authenticate with Perplexity using the CLI:

```bash
# In the activated virtual environment
pwm login
```

This will open a browser window for email OTP authentication. Follow the prompts
to complete the login process. The authentication token will be stored locally
and used by the adapter.

**Important**: Never share your authentication token or include it in any files.
The adapter is designed to never expose tokens in output, receipts, or logs.

## Usage

### Check Mode

Verify that the dependency is installed and available without making any API calls:

```bash
python3 tools/perplexity-worker.py --check
```

This will:
- Check if `perplexity-web-mcp-cli` is installed
- Verify the version is exactly 0.16.1
- Report the installation status
- Exit with appropriate status code

**Note**: Check mode never reads authentication tokens or makes network calls.

### Query Mode

Execute a research query using a task file:

```bash
python3 tools/perplexity-worker.py --model glm53 --receipt-dir ./receipts task.txt
```

**Options:**
- `--model`: Model to use (`glm53` or `kimi_k3`)
- `--receipt-dir`: Directory for receipt files (optional)
- `--bound`: Timeout in seconds (default: 300)
- `--stdout-size`: Maximum stdout size in bytes (default: 1048576 = 1MiB)

### Supported Models

| CLI Argument | Model Identifier | Thinking Identifier |
|--------------|------------------|---------------------|
| `glm53`      | `glm_5_3`        | `glm_5_3_thinking`  |
| `kimi_k3`    | `kimi_k3`        | `kimik3thinking`    |

**Important Notes:**
- The direct declared model is **not** server-verified as the effective model
- Receipts will state `effective_model: unknown` unless the actual response proves otherwise
- No fallback from unsupported or denied models is implemented

## Configuration

### agents.conf Examples

For research use, you can configure agents to use the Perplexity adapter:

```ini
# Research agent using Perplexity GLM-5-3
[agent:perplexity-glm]
command = python3 tools/perplexity-worker.py --model glm53 --receipt-dir ${UNIO_CONF_DIR}/receipts

# Research agent using Perplexity Kimi-K3
[agent:perplexity-kimi]
command = python3 tools/perplexity-worker.py --model kimi_k3 --receipt-dir ${UNIO_CONF_DIR}/receipts

# Group both Perplexity models to one budget group
[budget:perplexity]
agents = perplexity-glm,perplexity-kimi
max_concurrent = 1
```

### Budget Group Configuration

To use the Perplexity adapter with Unio's budget system:

```ini
# In your agents.conf
[budget:perplexity]
agents = perplexity-glm,perplexity-kimi
max_concurrent = 1
budget_group = perplexity

# This ensures only one Perplexity workflow runs at a time
# in low tier mode (one workflow per shared provider/account budget)
```

## Transport and Lab Distinction

- **Transport**: `PerplexityPro` - indicates the adapter is using Perplexity's Pro service
- **Lab**: The actual model lab (GLM lab for `glm_5_3`, Kimi lab/Moonshot for `kimi_k3`)

The adapter distinguishes between:
- **Transport Perplexity**: The service being used
- **GLM lab**: The lab that developed the GLM-5-3 model
- **Kimi lab/Moonshot**: The lab that developed the Kimi-K3 model

**Important**: No native final review acceptance is claimed from unverified effective labs.
The adapter does not make cross-lab review proofs.

## Receipt Generation

When `--receipt-dir` is specified, the adapter generates JSON receipt files with
sanitized metadata. Receipt files are named using the pattern:

```
YYYYMMDD-TASKHASH-perplexity-receipt.json
```

### Receipt Contents

Each receipt contains:

```json
{
  "source": "task_hash",
  "date": "2026-10-09T12:34:56.789012",
  "requested_model": "glm53",
  "configured_identifier": "glm_5_3_thinking",
  "transport": "PerplexityPro",
  "budget_group": "perplexity",
  "effective_model": "unknown",
  "outcome": "success",
  "exit_code": 0,
  "elapsed_seconds": 1.234,
  "bound_seconds": 300,
  "source_only_offline_claim": true
}
```

**Security Notes:**
- No tokens are ever included in receipts
- No prompts are included in receipts
- No raw answers are included in receipts
- No raw configuration is included in receipts
- The `source_only_offline_claim` field indicates this was a source-only operation

## Error Handling

The adapter maps various error conditions to clear, safe states:

| Error Condition | Exit Code | Description |
|----------------|-----------|-------------|
| Missing dependency | 1 | `perplexity-web-mcp-cli` not installed |
| Version mismatch | 2 | Wrong version of `perplexity-web-mcp-cli` |
| Import error | 3 | Error importing the module |
| Authentication missing | 4 | No Perplexity token found |
| Unsupported model | 5 | Model not in supported list |
| Timeout | 6 | Query exceeded time bound |
| Stdout overflow | 7 | Output exceeded size limit |
| Invalid JSON | 8 | Response contained invalid JSON |
| Invalid bounds | 9 | Invalid timeout or size bounds |
| Child error | 10 | General child process error |

## Direct Library Route

The adapter uses the **direct library route** to disable retries and ensure predictable behavior:

- `ClientConfig(max_retries=0)` - No automatic retries
- `logging_level="DISABLED"` - No logging output
- `rotate_fingerprint=False` - No fingerprint rotation
- `timeout=bound` - Uses the specified timeout bound

This approach avoids issues with:
- `pwm ask` not exposing `ClientConfig.max_retries`
- `shared.ask` rereading token/retries on auth failure
- SmartRouter/council/deep research/ancillary citation GETs
- Multiple HTTP requests per ask

**Note**: One `ask()` call is **not** one HTTP request. The library may make
ancillary requests (e.g., for citations). This is documented in the receipt.

## File Handling

### Task Files

- Must be regular files (not directories or symlinks)
- Must be non-empty
- Must be valid UTF-8 text
- Can contain path spaces
- Can be large files (tested up to 10MiB)

### Receipt Directories

- Created if they don't exist
- Must be directories (not files)
- Receipt files are never overwritten (unique names based on task hash and date)

## Security and Safety

### No Automatic Installation

The adapter **never** automatically installs dependencies. The owner must:
1. Create a virtual environment
2. Install `perplexity-web-mcp-cli==0.16.1`
3. Run `pwm login` for authentication

### No Network Calls in Check Mode

The `--check` option only verifies:
- Package installation
- Package version
- Import availability

It **never**:
- Reads authentication tokens
- Makes network calls
- Contacts Perplexity servers

### No Token Exposure

Authentication tokens are:
- Loaded once per query
- Never logged
- Never included in receipts
- Never included in output
- Never passed to child processes unnecessarily

### Bounded Execution

All operations are bounded by:
- **Time**: Configurable timeout (default: 300 seconds)
- **Output size**: Configurable stdout size (default: 1MiB)
- **Process isolation**: Child processes are killed on timeout

## Comparison with Community Connectors

### perplexity-web-mcp-cli 0.16.1 (Preferred)

- **License**: MIT
- **Authentication**: Browser-based OTP via `pwm login`
- **Model mapping**: Accurate and up-to-date
- **Features**: Full Perplexity Pro API support
- **Status**: Actively maintained

### perplexity-subscription-mcp 0.1.2 (Not Recommended)

- **Authentication**: Manual browser cookie export
- **Model mapping**: Obsolete (no GLM-5-3/Kimi-K3 support)
- **CORS**: Permissive dev REST CORS
- **Status**: Outdated

**Recommendation**: Use `perplexity-web-mcp-cli` 0.16.1 as the primary dependency.

## Official References

- [Perplexity Help Center - Advanced AI Models](https://www.perplexity.ai/help-center/en/articles/10354919-what-advanced-ai-models-are-included-in-my-subscription)
- [Perplexity Help Center - Subscription Plans](https://www.perplexity.ai/help-center/en/articles/11187416-which-perplexity-subscription-plan-is-right-for-you)

**Note**: The Perplexity API is separately billed. This adapter uses your existing
Pro web allowance only. The static catalog does not prove account access.

## Limitations

1. **No Server Verification**: The declared model is not server-verified as the effective model
2. **No Cross-Lab Proofs**: No native final review acceptance from unverified effective labs
3. **No Tool Calling**: The pinned upstream API server has tool calling disabled
4. **No Auto-Fallback**: No fallback from unsupported or denied models
5. **No Retry Logic**: Retries are explicitly disabled (`max_retries=0`)

## Future Work

- Integration with the full coding harness path (currently disabled tool calling)
- Enhanced model verification and effective model detection
- Support for additional Perplexity models as they become available
- Improved citation handling and metadata extraction

## Changelog

See `changelog.d/PERPLEXITY-ADAPTER-MISTRAL35-1.md` for the initial implementation details.

---

*This integration is designed for research use and requires manual installation and
authentication by the repository owner. No automated dependency installation,
network calls, or token handling is performed without explicit user action.*