"""
Enhanced Email Testing Script - PhishTank Integration
Tests the NLPAgent with either local sample emails or real PhishTank data.
"""
import json
import time
import os
import sys
from typing import List, Dict
from nlp_agent.agent import NLPAgent
from nlp_agent.schemas import PhishResult

# Import local test emails
from test_emails_automation import TEST_EMAILS, MockAgent, normalize_result, process_email_sync

# Try importing PhishTank integration
try:
    from phishtank_integration import load_phishtank_emails
    PHISHTANK_AVAILABLE = True
except ImportError:
    PHISHTANK_AVAILABLE = False
    print("[!] PhishTank integration not available. Install 'requests' package to use it.")


def run_tests_with_emails(emails: List[Dict], test_name: str = "Test Suite", agent=None):
    """
    Run tests with a given set of emails.
    
    Args:
        emails: List of email dicts
        test_name: Name of the test suite
        agent: NLPAgent instance (will create MockAgent if None)
        
    Returns:
        Test results list
    """
    print("\n" + "="*80)
    print(f"[*] {test_name} - RUNNING")
    print("="*80)
    print(f"Total emails to process: {len(emails)}\n")
    
    if agent is None:
        agent = MockAgent()
        print("[i] Using MockAgent for testing\n")
    
    results = []
    start_total = time.time()
    
    # Configurable delay
    DELAY = float(os.getenv("EMAIL_REQUEST_DELAY", "0.5"))
    FALLBACK_THRESHOLD = int(os.getenv("QUOTA_FALLBACK_THRESHOLD", "2"))
    consecutive_quota_errors = 0
    fallback_triggered = False
    
    for email_data in emails:
        # Auto-fallback on quota errors
        if fallback_triggered and not isinstance(agent, MockAgent):
            agent = MockAgent()
        
        result = process_email_sync(agent, email_data)
        
        # Detect quota errors
        if result.get("status") == "error":
            err = str(result.get("error", "")).lower()
            is_quota = any(k in err for k in ("quota", "429", "rate limit", "resourceexhausted", "exceeded your current quota"))
            if is_quota:
                consecutive_quota_errors += 1
                print(f"[!] Detected quota-like error (count={consecutive_quota_errors}): {result.get('error')}")
                if consecutive_quota_errors >= FALLBACK_THRESHOLD and not fallback_triggered:
                    print("[*] Quota threshold reached -- switching to MockAgent for remaining emails.")
                    fallback_triggered = True
                    agent = MockAgent()
                    print("[*] Reprocessing current email with MockAgent...")
                    result = process_email_sync(agent, email_data)
                results.append(result)
            else:
                consecutive_quota_errors = 0
                results.append(result)
        else:
            consecutive_quota_errors = 0
            results.append(result)
        
        time.sleep(DELAY)
    
    total_elapsed = time.time() - start_total
    
    # Summary statistics
    print(f"\n{'='*80}")
    print("[*] TEST SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]
    
    if successful:
        correct = [r for r in successful if r.get("match", False)]
        accuracy = (len(correct) / len(successful)) * 100
        print(f"Total processed: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Accuracy: {accuracy:.1f}% ({len(correct)}/{len(successful)})")
    else:
        print(f"Total processed: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
    
    print(f"Total time: {total_elapsed:.2f}s")
    if len(results) > 0:
        print(f"Average time per email: {(total_elapsed / len(results)):.2f}s\n")
    
    # Results table
    print(f"{'ID':<4} {'Predicted':<12} {'Expected':<12} {'Match':<10}")
    print("-" * 40)
    for r in results:
        if r["status"] == "success":
            match_str = "[OK]" if r["match"] else "[XX]"
            print(f"{r['email_id']:<4} {r['predicted']:<12} {r['expected']:<12} {match_str:<10}")
        else:
            print(f"{r['email_id']:<4} ERROR: {r.get('error', 'Unknown')[:30]}")
    
    return results


def main():
    """Main entry point."""
    
    # Determine which data source to use
    data_source = os.getenv("TEST_DATA_SOURCE", "local").lower()
    phishtank_count = int(os.getenv("PHISHTANK_COUNT", "20"))
    use_mock = os.getenv("USE_MOCK_AGENT", "0").lower() in ("1", "true", "yes")
    use_real_agent = not use_mock
    
    print("\n" + "="*80)
    print("[*] PHISHING EMAIL DETECTION - ENHANCED TEST SUITE")
    print("="*80)
    print(f"Configuration:")
    print(f"  Data source: {data_source}")
    print(f"  Mock mode: {use_mock}")
    print(f"  PhishTank available: {PHISHTANK_AVAILABLE}")
    print()
    
    # Load emails based on source
    if data_source == "phishtank":
        if not PHISHTANK_AVAILABLE:
            print("[-] PhishTank data source requested but 'requests' package not installed.")
            print("[*] Install with: pip install requests")
            sys.exit(1)
        
        try:
            print("[*] Loading PhishTank data...")
            emails = load_phishtank_emails(count=phishtank_count, use_cache_only=False)
            if not emails:
                print("[-] Failed to load PhishTank emails, falling back to local data")
                emails = TEST_EMAILS
            else:
                print(f"[+] Loaded {len(emails)} emails from PhishTank")
        except Exception as e:
            print(f"[-] PhishTank load failed: {e}")
            print("[*] Falling back to local test emails")
            emails = TEST_EMAILS
    else:
        # Use local test emails
        emails = TEST_EMAILS
        print(f"[+] Using {len(emails)} local test emails")
    
    # Initialize agent
    if use_real_agent:
        try:
            agent = NLPAgent()
            print("[+] NLPAgent initialized successfully\n")
        except Exception as e:
            print(f"[-] Failed to initialize agent: {e}")
            print("[*] Falling back to MockAgent")
            agent = MockAgent()
    else:
        agent = MockAgent()
        print("[i] Using MockAgent\n")
    
    # Run tests
    results = run_tests_with_emails(emails, test_name=f"{data_source.upper()} Email Tests", agent=agent)
    
    # Save results
    output_file = f"test_results_{data_source}_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[+] Results saved to: {output_file}")


if __name__ == "__main__":
    main()
