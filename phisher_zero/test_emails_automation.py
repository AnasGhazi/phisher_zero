"""
Test emails automation script
Feeds emails into the NLPAgent sequentially with proper async handling
"""
import asyncio
import json
import time
import os
from nlp_agent.agent import NLPAgent
from nlp_agent.schemas import PhishResult

# Extended test email dataset
TEST_EMAILS = [
    {
        "id": 1,
        "email": "Dear user, your account has been compromised. Click here to reset: http://fakebank-login.com",
        "expected": "phishing"
    },
    {
        "id": 2,
        "email": "Team — Reminder: monthly meeting tomorrow at 2pm. Agenda attached.",
        "expected": "legitimate"
    },
    {
        "id": 3,
        "email": "Hello, you won a prize! Verify your identity by providing your account password.",
        "expected": "phishing"
    },
    {
        "id": 4,
        "email": "Hi John, your Amazon order #123456 has been shipped. Track it here: https://amazon.com/orders",
        "expected": "legitimate"
    },
    {
        "id": 5,
        "email": "URGENT: Confirm your PayPal account details within 24 hours or lose access. Click: http://paypal-confirm-now.com",
        "expected": "phishing"
    },
    {
        "id": 6,
        "email": "Welcome to Netflix! Your subscription is active. Enjoy your shows.",
        "expected": "legitimate"
    },
    {
        "id": 7,
        "email": "Your package delivery failed. Click here to reschedule: http://delivery-reschedule-verify.org/?id=user",
        "expected": "phishing"
    },
    {
        "id": 8,
        "email": "Thanks for your purchase! Your receipt is attached. Order #9876543.",
        "expected": "legitimate"
    },
]

def normalize_result(result):
    """Normalize result to dict for consistent output."""
    if hasattr(result, "model_dump"):
        return result.model_dump()
    elif hasattr(result, "dict"):
        return result.dict()
    elif isinstance(result, dict):
        return result
    else:
        return {"raw": str(result)}


class MockAgent:
    """Simple rule-based mock agent for offline testing and fallback."""
    def analyze_email(self, email_text: str) -> PhishResult:
        t = email_text.lower()
        score = 0
        reasons = []
        if any(k in t for k in ("click here", "verify", "confirm", "password", "urgent", "won a prize", "account has been")):
            score = 1
            reasons.append("Contains urgent CTA or credential request")
        if "http://" in t and "https://" not in t:
            score = 1
            reasons.append("Contains unsecured http link")
        if score == 0:
            reasons.append("No obvious phishing indicators")
        return PhishResult(is_phishing=score, reason="; ".join(reasons))

def process_email_sync(agent, email_data):
    """Process a single email synchronously."""
    email_id = email_data["id"]
    email_text = email_data["email"]
    expected = email_data["expected"]
    
    print(f"\n{'='*80}")
    print(f"Processing Email #{email_id}")
    print(f"{'='*80}")
    print(f"Text: {email_text[:100]}..." if len(email_text) > 100 else f"Text: {email_text}")
    print(f"Expected: {expected.upper()}")
    
    try:
        start_time = time.time()
        result = agent.analyze_email(email_text)
        elapsed = time.time() - start_time
        
        normalized = normalize_result(result)
        is_phishing = normalized.get("is_phishing", 1)
        reason = normalized.get("reason", "")
        
        # Determine if classification matches expectation
        predicted = "phishing" if is_phishing == 1 else "legitimate"
        match = "[OK] CORRECT" if predicted == expected else "[XX] INCORRECT"
        
        print(f"Predicted: {predicted.upper()}")
        print(f"Result: {match}")
        print(f"Reason: {reason}")
        print(f"Response Time: {elapsed:.2f}s")
        
        return {
            "email_id": email_id,
            "status": "success",
            "predicted": predicted,
            "expected": expected,
            "match": predicted == expected,
            "reason": reason,
            "elapsed_sec": elapsed
        }
        
    except Exception as e:
        print(f"[-] ERROR: {str(e)}")
        return {
            "email_id": email_id,
            "status": "error",
            "error": str(e)
        }

def run_tests():
    """Run all email tests sequentially."""
    print("\n" + "="*80)
    print("[*] PHISHING EMAIL DETECTION - AUTOMATION TEST SUITE")
    print("="*80)
    print(f"Total emails to process: {len(TEST_EMAILS)}\n")
    
    # Configurable delay between requests (seconds) to avoid hitting rate limits
    DELAY = float(os.getenv("EMAIL_REQUEST_DELAY", "0.5"))

    # If set, run a local mock agent instead of calling the Gemini API.
    # Useful for offline testing or when you've hit API quota limits.
    MOCK_MODE = os.getenv("USE_MOCK_AGENT", "0").lower() in ("1", "true", "yes")

    if MOCK_MODE:
        agent = MockAgent()
        print("[i] Running in MOCK_MODE - no network calls will be made\n")
    else:
        try:
            agent = NLPAgent()
            print("[+] NLPAgent initialized successfully\n")
        except Exception as e:
            print(f"[-] Failed to initialize agent: {e}")
            return

    # Auto-fallback configuration: after this many consecutive quota errors, switch to MockAgent
    FALLBACK_THRESHOLD = int(os.getenv("QUOTA_FALLBACK_THRESHOLD", "2"))
    consecutive_quota_errors = 0
    fallback_triggered = False
    
    results = []
    start_total = time.time()
    
    # Process each email sequentially (important: wait for response before next call)
    for email_data in TEST_EMAILS:
        # If fallback already triggered, ensure we're using MockAgent
        if fallback_triggered:
            agent = MockAgent()

        result = process_email_sync(agent, email_data)

        # Detect quota-like errors and optionally trigger fallback
        if result.get("status") == "error":
            err = str(result.get("error", "")).lower()
            is_quota = any(k in err for k in ("quota", "429", "rate limit", "resourceexhausted", "exceeded your current quota"))
            if is_quota:
                consecutive_quota_errors += 1
                print(f"[!] Detected quota-like error (count={consecutive_quota_errors}): {result.get('error')}")
                # If threshold reached, switch to mock and re-run the current email with MockAgent
                if consecutive_quota_errors >= FALLBACK_THRESHOLD and not fallback_triggered:
                    print("[*] Quota threshold reached -- switching to MockAgent for remaining emails.")
                    fallback_triggered = True
                    agent = MockAgent()
                    print("[*] Reprocessing current email with MockAgent...")
                    # Reprocess current email with mock agent
                    result = process_email_sync(agent, email_data)
                    results.append(result)
                else:
                    # don't append the original failed result yet; wait and continue
                    results.append(result)
            else:
                # non-quota error; append and reset quota counter
                consecutive_quota_errors = 0
                results.append(result)
        else:
            consecutive_quota_errors = 0
            results.append(result)

        time.sleep(DELAY)  # Configurable delay between requests
    
    total_elapsed = time.time() - start_total
    
    # Summary statistics
    print(f"\n{'='*80}")
    print("[*] TEST SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]
    correct = [r for r in successful if r.get("match", False)]
    
    print(f"Total processed: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        accuracy = (len(correct) / len(successful)) * 100
        print(f"Accuracy: {accuracy:.1f}% ({len(correct)}/{len(successful)})")
    
    print(f"Total time: {total_elapsed:.2f}s")
    print(f"Average time per email: {(total_elapsed / len(results)):.2f}s\n")
    
    # Detailed results table
    print(f"{'ID':<4} {'Predicted':<12} {'Expected':<12} {'Match':<10} {'Time(s)':<10}")
    print("-" * 50)
    for r in results:
        if r["status"] == "success":
            match_str = "[OK]" if r["match"] else "[XX]"
            time_str = f"{r['elapsed_sec']:.2f}"
            print(f"{r['email_id']:<4} {r['predicted']:<12} {r['expected']:<12} {match_str:<10} {time_str:<10}")
        else:
            print(f"{r['email_id']:<4} ERROR - {r.get('error', 'Unknown error')[:40]}")
    
    # Save results to JSON
    output_file = "test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Results saved to: {output_file}")

if __name__ == "__main__":
    run_tests()
