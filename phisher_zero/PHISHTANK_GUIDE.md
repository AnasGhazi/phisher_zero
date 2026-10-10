# PhishTank Integration Guide

This module integrates real phishing data from **PhishTank** (https://www.phishtank.com) for testing and validating your NLP-based phishing detection agent.

## Overview

PhishTank is a free community-driven database of phishing and malware data. It provides:
- **Real-world phishing URLs** verified by the community
- **Regular updates** with new threats
- **Free API access** for research and security testing
- **Large dataset** for comprehensive validation

## Setup

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

This includes the `requests` package needed for PhishTank API calls.

### 2. (Optional) Get a PhishTank API Key

For unlimited access and higher rate limits:

1. Go to: https://www.phishtank.com/developer_info.php
2. Sign up for a free account
3. Generate an API key
4. Add to your `.env` file:

```
PHISHTANK_API_KEY=your_api_key_here
```

Without an API key, the module uses built-in sample phishing URLs and automatically falls back gracefully.

## Usage

### Quick Test with Built-in Data

Run tests using pre-loaded sample phishing URLs (no internet required):

```powershell
$env:TEST_DATA_SOURCE = "phishtank"
$env:PHISHTANK_COUNT = "10"
$env:USE_MOCK_AGENT = "1"
python test_with_phishtank.py
```

### Test with Real Gemini API

```powershell
$env:TEST_DATA_SOURCE = "phishtank"
$env:PHISHTANK_COUNT = "20"
python test_with_phishtank.py
```

This will:
1. Fetch real phishing data from PhishTank (or use cache)
2. Generate synthetic phishing emails from the URLs
3. Test your agent against them
4. Save results to `test_results_phishtank_*.json`

### Test with Local Data (Default)

```powershell
$env:TEST_DATA_SOURCE = "local"
$env:USE_MOCK_AGENT = "1"
python test_with_phishtank.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEST_DATA_SOURCE` | `local` | Data source: `local` or `phishtank` |
| `PHISHTANK_COUNT` | `20` | Number of phishing samples to load |
| `PHISHTANK_API_KEY` | - | Optional API key for higher rate limits |
| `USE_MOCK_AGENT` | `0` | Use mock agent (1) or real Gemini (0) |
| `EMAIL_REQUEST_DELAY` | `0.5` | Delay between API requests in seconds |
| `QUOTA_FALLBACK_THRESHOLD` | `2` | Quota errors before auto-fallback to mock |

## How It Works

### Data Flow

```
PhishTank Database
       ↓
[API or Built-in]
       ↓
phishtank_integration.py
   ├─ Fetch URLs
   ├─ Cache locally
   └─ Generate synthetic emails
       ↓
test_with_phishtank.py
   ├─ Load emails
   ├─ Pass to NLPAgent
   ├─ Collect predictions
   └─ Save results
```

### Synthetic Email Generation

For each phishing URL from PhishTank, the system generates a realistic phishing email:

```
Dear Customer,

We have detected unusual activity on your {target} account.
Please verify your credentials immediately to prevent account suspension.

Click here to verify your account: {url}

This is urgent. Your account will be locked if not verified within 24 hours.

Best regards,
Account Security Team
```

This ensures your agent is tested on realistic phishing content, not just URLs.

## Caching

- PhishTank data is cached in `phishtank_cache.json` for offline use
- First run fetches from API (if available), subsequent runs use cache
- To force refresh: Delete `phishtank_cache.json` or call with `force_refresh=True`

## Handling Rate Limits

PhishTank has rate limits. If you hit them:

1. **Without API key**: Limited requests (use cache)
2. **With API key**: Higher limits (50+ requests/minute)
3. **Automatic fallback**: If API fails, uses built-in sample data

## Examples

### Compare Local vs PhishTank Performance

```powershell
# Test 1: Local data with real agent
python test_with_phishtank.py

# Test 2: PhishTank data with real agent
$env:TEST_DATA_SOURCE = "phishtank"
$env:PHISHTANK_COUNT = "50"
python test_with_phishtank.py

# Compare test_results_local_*.json vs test_results_phishtank_*.json
```

### Full Testing Pipeline

```powershell
# Set your API key
$env:PHISHTANK_API_KEY = "your_key_here"

# Test with increasing dataset sizes
$env:PHISHTANK_COUNT = "10"; python test_with_phishtank.py
$env:PHISHTANK_COUNT = "50"; python test_with_phishtank.py
$env:PHISHTANK_COUNT = "100"; python test_with_phishtank.py
```

## Troubleshooting

### "API fetch failed"
- ✅ This is normal — built-in fallback will be used
- Install `requests`: `pip install requests`
- Check internet connection
- Consider getting a PhishTank API key

### "No data loaded"
- Delete `phishtank_cache.json` and try again
- Verify internet connection for API fetch
- Check `PHISHTANK_COUNT` is not 0

### Slow Performance
- Use mock agent: `USE_MOCK_AGENT=1`
- Increase `EMAIL_REQUEST_DELAY` if hitting rate limits
- Use smaller `PHISHTANK_COUNT` for testing

## File Reference

| File | Purpose |
|------|---------|
| `phishtank_integration.py` | Core module for fetching and processing PhishTank data |
| `test_with_phishtank.py` | Main test runner with PhishTank integration |
| `phishtank_cache.json` | Local cache of PhishTank data |
| `test_results_phishtank_*.json` | Test results with timestamps |

## See Also

- **PhishTank API Docs**: https://www.phishtank.com/developer_info.php
- **Test Automation**: `test_emails_automation.py`
- **NLP Agent**: `nlp_agent/agent.py`
