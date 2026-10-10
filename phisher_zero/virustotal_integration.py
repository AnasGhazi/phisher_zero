import base64
import requests
import os
from typing import Dict

def get_url_id(url: str) -> str:
    """Generate VirusTotal URL ID (URL-safe base64 without padding)."""
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    return url_id

def check_url_in_virustotal(url: str) -> Dict:
    """
    Check VirusTotal v3 API for a URL's malicious status.
    Returns a dictionary with 'virustotal_match' and 'confidence'.
    """
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    if not api_key:
        print("[!] VIRUSTOTAL_API_KEY not found in environment.")
        return {"virustotal_match": False, "confidence": 0.0, "stats": {}}
        
    url_id = get_url_id(url)
    endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"
    headers = {
        "x-apikey": api_key,
        "Accept": "application/json"
    }
    
    try:
        resp = requests.get(endpoint, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            
            # If any security vendor flagged it, we consider it a hit
            total_flags = malicious + suspicious
            is_match = total_flags > 0
            
            # Confidence is scaled based on how many engines flagged it.
            # E.g. 1 flag = 0.5, >=3 flags = 1.0 confidence
            if total_flags == 0:
                confidence = 0.0
            elif total_flags == 1:
                confidence = 0.5
            elif total_flags == 2:
                confidence = 0.8
            else:
                confidence = 1.0
                
            return {
                "virustotal_match": is_match,
                "confidence": confidence,
                "stats": stats
            }
        elif resp.status_code == 404:
            # The URL has not been scanned before. For the demo scope, treat as non-malicious (Unseen).
            return {"virustotal_match": False, "confidence": 0.0, "stats": {}}
        else:
            print(f"[!] VirusTotal API error {resp.status_code}: {resp.text}")
            return {"virustotal_match": False, "confidence": 0.0, "stats": {}}
            
    except Exception as e:
        print(f"[!] VirusTotal request failed: {e}")
        return {"virustotal_match": False, "confidence": 0.0, "stats": {}}
