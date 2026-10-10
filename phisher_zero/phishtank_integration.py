"""
PhishTank Integration Module
Fetches real phishing data from PhishTank API for testing and validation.
PhishTank: https://www.phishtank.com/
Note: For unlimited access, obtain a free API key at: https://www.phishtank.com/developer_info.php
"""
import os
import json
import requests
import hashlib
from typing import List, Dict, Optional

# PhishTank API endpoints
# Note: The actual data.phishtank.com endpoints require authentication or have usage limits
# For testing, we'll use a fallback approach with common phishing patterns
# You can get a free API key at: https://www.phishtank.com/developer_info.php
PHISHTANK_API_URL = "https://data.phishtank.com/data/online-valid.json"
PHISHTANK_CSV_URL = "https://data.phishtank.com/data/online-valid.csv"

# Built-in sample phishing data for fallback/testing
SAMPLE_PHISHING_URLS = [
    {"url": "http://secure-paypal-verify.com/login", "target": "PayPal"},
    {"url": "http://amazon-account-alert.net", "target": "Amazon"},
    {"url": "http://apple-id-verify-now.org", "target": "Apple"},
    {"url": "http://microsoft-365-login.xyz", "target": "Microsoft 365"},
    {"url": "http://gmail-verify-account.info", "target": "Gmail"},
    {"url": "http://dropbox-sync-error.com", "target": "Dropbox"},
    {"url": "http://linkedin-update-required.net", "target": "LinkedIn"},
    {"url": "http://facebook-confirm-identity.org", "target": "Facebook"},
    {"url": "http://netflix-billing-update.xyz", "target": "Netflix"},
    {"url": "http://steam-guard-verification.com", "target": "Steam"},
    {"url": "http://bank-of-america-verify.net", "target": "Bank of America"},
    {"url": "http://chase-security-alert.info", "target": "Chase"},
    {"url": "http://twitter-account-locked.org", "target": "Twitter"},
    {"url": "http://instagram-confirm-login.xyz", "target": "Instagram"},
    {"url": "http://ebay-verify-identity.com", "target": "eBay"},
]

class PhishTankManager:
    """Manages PhishTank data fetching and caching."""
    
    def __init__(self, cache_file: str = "phishtank_cache.json", api_key: Optional[str] = None):
        """
        Initialize PhishTank manager.
        
        Args:
            cache_file: Local file to cache PhishTank data
            api_key: Optional PhishTank API key for authentication (increases rate limits)
        """
        self.cache_file = cache_file
        self.api_key = api_key or os.getenv("PHISHTANK_API_KEY")
        self.data = None
        self.phishing_urls = set()
    
    def fetch_data(self, force_refresh: bool = False) -> List[Dict]:
        """
        Fetch PhishTank data from API or cache.
        
        Args:
            force_refresh: If True, ignore cache and fetch from API
            
        Returns:
            List of phishing entries from PhishTank
        """
        # Try loading from cache first
        if not force_refresh and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    self.data = json.load(f)
                    print(f"[+] Loaded {len(self.data)} entries from cache: {self.cache_file}")
                    return self.data
            except Exception as e:
                print(f"[!] Cache load failed: {e}, attempting to fetch from API...")
        
        # Fetch from API
        try:
            headers = {}
            if self.api_key:
                headers["X-PHT-API-KEY"] = self.api_key
                print(f"[*] Using PhishTank API key")
            
            print("[*] Fetching PhishTank data from API...")
            # Try multiple endpoints
            for url in [PHISHTANK_API_URL]:
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    response.raise_for_status()
                    self.data = response.json()
                    
                    # Cache the data
                    with open(self.cache_file, "w") as f:
                        json.dump(self.data, f)
                    
                    print(f"[+] Fetched and cached {len(self.data)} phishing entries")
                    return self.data
                except requests.exceptions.RequestException as e:
                    print(f"[!] Endpoint {url} failed: {e}")
                    continue
            
            # If API fails, use built-in sample data
            print("[*] API unavailable, using built-in sample phishing URLs")
            self.data = SAMPLE_PHISHING_URLS
            
            # Cache the sample data
            with open(self.cache_file, "w") as f:
                json.dump(self.data, f)
            
            return self.data
            
        except Exception as e:
            print(f"[-] Unexpected error: {e}")
            print("[*] Falling back to built-in sample data")
            self.data = SAMPLE_PHISHING_URLS
            return self.data
    
    def build_url_index(self):
        """Build a set of all known phishing URLs for quick lookup."""
        if not self.data:
            raise ValueError("No data loaded. Call fetch_data() first.")
        
        self.phishing_urls = set()
        for entry in self.data:
            if "url" in entry:
                self.phishing_urls.add(entry["url"])
        
        print(f"[+] Built index of {len(self.phishing_urls)} unique phishing URLs")
    
    def generate_email_from_phishing_url(self, entry: Dict, email_id: int) -> Dict:
        """
        Generate a synthetic phishing email from a PhishTank URL entry.
        
        Args:
            entry: PhishTank entry with URL and metadata
            email_id: ID for the generated email
            
        Returns:
            Email dict with id, email text, and expected classification
        """
        url = entry.get("url", "")
        target = entry.get("target", "Unknown")
        submission_time = entry.get("submission_time", "")
        
        # Generate a simple phishing email with the suspicious URL
        email_text = f"""
Dear Customer,

We have detected unusual activity on your {target} account. 
Please verify your credentials immediately to prevent account suspension.

Click here to verify your account: {url}

This is urgent. Your account will be locked if not verified within 24 hours.

Best regards,
Account Security Team
""".strip()
        
        return {
            "id": email_id,
            "email": email_text,
            "expected": "phishing",
            "source": "PhishTank",
            "target": target,
            "url": url,
            "submission_time": submission_time
        }
    
    def get_email_samples(self, count: int = 10, start_index: int = 0) -> List[Dict]:
        """
        Get email samples generated from PhishTank data.
        
        Args:
            count: Number of emails to generate
            start_index: Starting index in PhishTank data
            
        Returns:
            List of email dicts
        """
        if not self.data:
            raise ValueError("No data loaded. Call fetch_data() first.")
        
        emails = []
        for i, entry in enumerate(self.data[start_index:start_index+count]):
            email = self.generate_email_from_phishing_url(entry, start_index + i + 1)
            emails.append(email)
        
        return emails

    def check_url(self, url: str) -> Dict:
        """
        Check if a URL is in the PhishTank database.
        
        Args:
            url: The URL to check
            
        Returns:
            Dict containing phish_tank_match and confidence
        """
        if not self.data:
            self.fetch_data()
            
        # Ensure index is built
        if not self.phishing_urls:
            self.build_url_index()
            
        import urllib.parse
        
        # Clean both input and cache to match domain/path substrings easily
        input_clean = url.lower().replace("http://", "").replace("https://", "").replace("www.", "")
        
        is_match = False
        for phish_url in self.phishing_urls:
            phish_clean = phish_url.lower().replace("http://", "").replace("https://", "").replace("www.", "")
            
            # Substring match ensures that even if user adds parameters or paths, it detects the core threat
            if phish_clean in input_clean or input_clean in phish_clean:
                is_match = True
                break
        
        # If it's a match, confidence is high (1.0). Otherwise 0.0.
        confidence = 1.0 if is_match else 0.0
        
        return {
            "phish_tank_match": is_match,
            "confidence": confidence
        }

def check_url_in_phishtank(url: str) -> Dict:
    """
    Convenience function to check a URL against PhishTank.
    
    Args:
        url: URL to check
        
    Returns:
        Dict with match status and confidence
    """
    manager = PhishTankManager()
    try:
        return manager.check_url(url)
    except Exception as e:
        print(f"[!] PhishTank check failed: {e}")
        return {"phish_tank_match": False, "confidence": 0.0}



def load_phishtank_emails(count: int = 20, use_cache_only: bool = False) -> List[Dict]:
    """
    Convenience function to load PhishTank emails for testing.
    
    Args:
        count: Number of phishing emails to load
        use_cache_only: If True, only use cached data (don't fetch API)
        
    Returns:
        List of email dicts
    """
    manager = PhishTankManager()
    
    try:
        manager.fetch_data(force_refresh=False)
    except Exception as e:
        if use_cache_only:
            print(f"[-] use_cache_only=True but fetch failed: {e}")
            raise
        print(f"[!] Fetch failed: {e}")
        return []
    
    emails = manager.get_email_samples(count=count)
    return emails


if __name__ == "__main__":
    # Quick test
    print("[*] PhishTank Integration Test\n")
    
    try:
        emails = load_phishtank_emails(count=5)
        print(f"\n[+] Generated {len(emails)} sample emails:\n")
        for email in emails:
            print(f"  ID {email['id']}: Target={email['target']}, URL={email['url'][:50]}...")
    except Exception as e:
        print(f"[-] Error: {e}")
        print("\nNote: PhishTank fetch requires internet connection.")
        print("You can also run with cached data if available.")
