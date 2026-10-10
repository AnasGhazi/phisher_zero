# Phisher Zero

Phisher Zero is a multi-agent phishing detection system built as a Final Year Project. It has two parts: a Python/FastAPI backend and a Chrome extension. The backend scores email text and URLs with several independent agents and then combines the scores into one verdict. The extension sends the current page, or text you paste in, to the backend and shows the result.

```
phisher_zero/              Python backend (FastAPI + detection agents)
phisher_zero_chrome_ext/   Chrome extension (Manifest V3) frontend
```

---

## How it works

One request to `POST /analyze` runs through four agents in order:

```
                  email_text ──► NLP Agent ──────────────┐
                                                          ├─► Ensemble Agent ──► Explainer Agent ──► response
  url (optional) ──► URL Agent (heuristics + VirusTotal) ─┘
```

### 1. NLP Agent ([`nlp_agent/`](phisher_zero/nlp_agent))
Decides whether the email text reads like phishing.

- **Primary model:** the Hugging Face DistilBERT classifier [`cybersectony/phishing-email-detection-distilbert_v2.4.1`](https://huggingface.co/cybersectony/phishing-email-detection-distilbert_v2.4.1). The input is cut to 512 tokens. The agent reports `nlp_score = 1 − P(legitimate_email)`.
- **Fallback:** if the Hugging Face model can't be loaded, the agent asks Google Gemini instead, through LangChain, using the prompts in [`prompts.py`](phisher_zero/nlp_agent/prompts.py). Gemini returns a binary `is_phishing` label (0/1) and a reason.

### 2. URL Agent ([`url_agent/`](phisher_zero/url_agent))
Runs only when a `url` is provided.

- **Lexical features:** URL length, subdomain count, IP address used as the host, HTTPS or not, suspicious keywords (`login`, `verify`, `bank`, …), special characters, and a risky TLD (`.tk`, `.xyz`, `.top`, …).
- **Heuristic classifier:** a weighted rule-based score built from those features. It returns `ml_score` and a label.
- **VirusTotal v3 lookup** ([`virustotal_integration.py`](phisher_zero/virustotal_integration.py)): fetches the URL's last analysis stats. Confidence depends on how many engines flagged it as malicious or suspicious: 1 engine → 0.5, 2 → 0.8, 3 or more → 1.0. A URL VirusTotal has never seen counts as clean.
- **`url_risk_score`:** `1.0` if VirusTotal flagged the URL. Otherwise it is `0.3 × ml_score`, so the heuristics only play a minor role.

### 3. Ensemble Agent ([`ensemble_agent/`](phisher_zero/ensemble_agent))
Combines the scores using the weights and thresholds in [`config.py`](phisher_zero/config.py):

| Input | Weight (URL provided) | Weight (no URL) |
|---|---|---|
| NLP score | 0.60 | 1.00 |
| VirusTotal confidence | 0.30 | — |
| URL risk score | 0.10 | — |

- **Override:** if a URL is present and VirusTotal confidence is ≥ 0.9, the final score is forced to `1.0`.
- **Verdict:** `phishing` if score ≥ 0.70, `suspicious` if score ≥ 0.40, otherwise `safe`.

### 4. Explainer Agent ([`explainer_agent/`](phisher_zero/explainer_agent))
Turns the technical signals into an explanation a person can read. It sends the structured results to Gemini and asks for strict JSON with `summary`, `key_reasons`, `risk_level` (Low/Medium/High) and `recommended_action`. If Gemini isn't configured, fails, or returns JSON that won't parse, the agent writes the explanation from fixed rules instead.

---

## Chrome extension

The extension in [`phisher_zero_chrome_ext/`](phisher_zero_chrome_ext) is a Manifest V3 popup.

- **Scan button:**
  - By default it reads the active tab's URL and up to 5,000 characters of the page's visible text, then sends both to `/analyze`.
  - If you type email text or a URL into the manual input fields, those values replace the page's text and URL.
- **Results view:** a status card (Waiting / Analyzing / Safe / Phishing Detected / Error) and four agent cards:
  - NLP score
  - URL risk score and whether VirusTotal flagged it
  - Final ensemble score and verdict
  - The explainer's summary and recommended action

  A `suspicious` verdict shows up in the status card as a phishing warning.
- **Settings page:**
  - API base URL. On install it is set to `http://localhost:8000`.
  - Mock mode, which returns random sample results without calling the backend.
  - Dark mode.

---

## Getting started

### Prerequisites
- Python 3.11+ (developed with 3.12/3.13)
- A [Google Gemini API key](https://ai.google.dev/). **Required:** the NLP agent refuses to start without `GOOGLE_API_KEY`.
- A [VirusTotal API key](https://www.virustotal.com/gui/my-apikey). Optional, but without it every URL counts as "not flagged".
- Google Chrome

### 1. Run the backend

```bash
cd phisher_zero
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then edit .env
```

`.env` needs these values:

```env
GOOGLE_API_KEY=your_gemini_key
VIRUSTOTAL_API_KEY=your_virustotal_key
GEMINI_MODEL=gemini-2.5-flash
```

Then start the server:

```bash
python main.py
```

The API runs at `http://localhost:8000`, and interactive docs are at `http://localhost:8000/docs`. On the first start the server downloads the DistilBERT model from Hugging Face, which can take a minute.

### 2. Load the extension

1. Open `chrome://extensions/` and turn on **Developer mode**.
2. Click **Load unpacked** and select the `phisher_zero_chrome_ext` folder.
3. Pin the Phisher Zero icon. Open **Settings** and make sure the API base URL is `http://localhost:8000` and mock mode is off.
4. Open an email or web page and click **Scan**.

---

## API

### `GET /`
Health check. Returns `{"message": "Phisher Zero API is running."}`.

### `POST /analyze`

**Request**
```json
{
  "email_text": "Verify your account immediately to avoid suspension.",
  "url": "http://fake-bank-login.com"
}
```
`email_text` is required. `url` is optional; without it, only the NLP agent contributes to the score.

**Response** (shape)
```json
{
  "analysis": {
    "nlp": { "nlp_score": 0.97 },
    "url": {
      "url": "http://fake-bank-login.com",
      "features": { "length": 26, "has_https": false, "suspicious_keywords": ["login", "bank"], "...": "..." },
      "virustotal": { "virustotal_match": false, "confidence": 0.0, "stats": {} },
      "ml_prediction": { "ml_score": 0.5, "label": "legitimate" },
      "url_risk_score": 0.15,
      "explanation": "The URL is suspicious because it lacks secure HTTPS encryption, and contains suspicious keywords (login, bank)."
    },
    "ensemble": {
      "final_score": 0.597,
      "verdict": "suspicious",
      "confidence": 0.403,
      "contributions": { "url_agent": 0.1, "nlp_agent": 0.6, "virustotal": 0.3 },
      "explanation": "Moderate indicators of phishing; exercise caution."
    }
  },
  "explanation": {
    "summary": "...",
    "key_reasons": ["..."],
    "risk_level": "Medium",
    "recommended_action": "..."
  }
}
```

Example call:
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"email_text": "Verify your account immediately to avoid suspension.", "url": "http://fake-bank-login.com"}'
```

---

## Testing and evaluation scripts

All scripts run from inside `phisher_zero/`. They test the NLP agent's Gemini path (`analyze_email`), not the full `/analyze` pipeline.

| Script | What it does |
|---|---|
| `run_local.py` | Runs the NLP agent on three sample emails and prints the results. |
| `test_emails_automation.py` | Runs a labelled set of sample emails and compares predictions to expected labels. Writes `test_results.json`. |
| `test_with_phishtank.py` | Same as above, but with `TEST_DATA_SOURCE=phishtank` it builds test emails from live PhishTank phishing URLs. Writes `test_results_<source>_<timestamp>.json`. |
| `phishtank_integration.py` | Downloads and caches the PhishTank feed in `phishtank_cache.json` (gitignored), generates phishing emails from it, and can check a URL against the feed. Uses built-in sample URLs if the feed can't be reached. |

Settings you can change with environment variables:

| Variable | Effect |
|---|---|
| `USE_MOCK_AGENT=1` | Runs offline with a keyword-based mock agent. |
| `EMAIL_REQUEST_DELAY` | Seconds to wait between Gemini calls. |
| `QUOTA_FALLBACK_THRESHOLD` | Number of consecutive quota errors before switching to the mock agent. |
| `PHISHTANK_COUNT` | Number of PhishTank emails to generate. |
| `PROMPT_NAME` | Which Gemini prompt to use: `EMAIL_WORKFLOW_PROMPT` or `PROMPT`. |

---

## Configuration

These values in [`phisher_zero/config.py`](phisher_zero/config.py) can be overridden from `.env`:

| Setting | Default |
|---|---|
| `NLP_WEIGHT` / `VIRUSTOTAL_WEIGHT` / `URL_WEIGHT` | 0.60 / 0.30 / 0.10 |
| `PHISHING_THRESHOLD` | 0.70 |
| `SUSPICIOUS_THRESHOLD` | 0.40 |
| `GEMINI_MODEL` | `gemini-2.5-flash` |

---

## Known limitations

- **URL classifier:** it is weighted heuristics, not a trained model. The domain-age feature is a placeholder (30 days for a risky TLD, otherwise 365) rather than a real WHOIS lookup.
- **Gemini model default:** the NLP agent's Gemini fallback defaults to `gemini-1.5-flash`, while the explainer defaults to `gemini-2.5-flash`. Set `GEMINI_MODEL` in `.env` so both use the same model.
- **Startup requirement:** `GOOGLE_API_KEY` is required at startup even when the Hugging Face model handles all the scoring.
- **CORS:** it is open (`allow_origins=["*"]`), which is fine for local development but should be restricted before deployment.
- **Unit tests:** `tests/test_agent.py` is an empty placeholder; there are no unit tests yet.

---

## Tech stack

**Backend:** Python, FastAPI, Uvicorn, Pydantic, Hugging Face Transformers + PyTorch, LangChain, Google Gemini (`langchain-google-genai`, `google-generativeai`), VirusTotal API v3, PhishTank (evaluation only)

**Frontend:** Chrome Extension Manifest V3, vanilla JavaScript, Tailwind CSS
