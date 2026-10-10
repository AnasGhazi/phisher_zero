# Phisher Zero

Phisher Zero is a production-ready, modular multi-agent phishing detection system. It actively analyzes emails and web pages to detect phishing attempts using a combination of natural language processing, URL analysis, and threat intelligence (like PhishTank).

## Project Structure

The project is broken into two main components:
1. **`phisher_zero`**: The Python/FastAPI backend containing the core multi-agent phishing detection logic.
2. **`phisher_zero_chrome_ext`**: A Chrome extension frontend designed to analyze browser page contents and integrate directly with the backend.

---

## 🚀 Recent Changes & Features Implemented

During the recent development phase, the following major updates were implemented to complete the Phisher Zero architecture:

1. **Multi-Agent Backend System (`phisher_zero`)**: 
   - **NLP Agent**: Analyzes the semantic content and language of emails to detect urgency, typical phishing keywords, and manipulative tone.
   - **URL Agent & PhishTank Integration**: Extracts URLs from content and checks their risk score alongside cross-referencing against the PhishTank database for known malicious links.
   - **Ensemble Agent**: Aggregates the scores from the NLP Agent, URL risk score, and PhishTank confidence to produce a final verdict.
   - **Explainer Agent**: Generates a human-readable explanation of why a particular piece of content was flagged as phishing or safe.
   - **FastAPI Endpoints**: Exposed a `/analyze` POST endpoint in `main.py` to allow the frontend extension/web app to submit data for analysis.

2. **Chrome Extension Integration (`phisher_zero_chrome_ext`)**:
   - Designed to run within the user's browser, extract live web content natively, and directly pass it onto the backend for live analysis.
   - Tied backend responses into the extension popup logic.

---

## 🛠️ How to Run the Project Locally

To run the full end-to-end system, you will need to start the Python Backend, and load the Chrome Extension.

### 1. Run the Backend API (FastAPI)

The backend handles the actual machine learning, multi-agent logic, and PhishTank requests. 

Open a terminal and run:
```bash
cd phisher_zero
source .venv/bin/activate
python main.py
```
*(The backend will start locally on `http://127.0.0.1:8000`)*

### 2. Load the Chrome Extension

The Chrome extension monitors the active browser sessions and works hand-in-hand with the local backend.

1. Open your Google Chrome browser.
2. Type `chrome://extensions/` into the URL bar and hit Enter.
3. In the top right corner, toggle **Developer mode** ON.
4. Click the **Load unpacked** button in the top left.
5. Select the `phisher_zero_chrome_ext` directory located in your project folder (`/Users/anasghazi/Desktop/phisher_zero_fyp2/phisher_zero_chrome_ext`).
6. The Phisher Zero icon should now appear in your browser's extension bar. You can pin it for easy access!

---

## API Usage Example

Once the backend is running, you can test it directly using `curl` or Postman:

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{
           "email_text": "Verify your account immediately to avoid suspension at http://fake-bank-login.com.",
           "url": "http://fake-bank-login.com"
         }'
```
