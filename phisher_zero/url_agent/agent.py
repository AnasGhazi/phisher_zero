import urllib.parse
import re
from typing import Dict, Any

from virustotal_integration import check_url_in_virustotal

class URLAgent:
    """Agent responsible for analyzing URLs for phishing indicators."""
    
    SUSPICIOUS_KEYWORDS = ["login", "verify", "secure", "update", "account", "signin", "bank", "confirm"]
    RISKY_TLDS = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".site", ".club"]
    
    def __init__(self):
        pass

    def extract_features(self, url: str) -> Dict[str, Any]:
        """Extract structural and lexical features from the URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
        except Exception:
            domain = ""
            path = ""
            
        # 1. URL Length
        length = len(url)
        
        # 2. Number of subdomains (rough estimate by counting dots in domain)
        # Exclude 'www' usually
        clean_domain = domain.replace("www.", "")
        num_subdomains = max(0, clean_domain.count(".") - 1)
        
        # 3. Presence of IP address instead of domain
        ip_pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
        has_ip = bool(ip_pattern.match(clean_domain))
        
        # 4. HTTPS usage
        has_https = url.lower().startswith("https://")
        
        # 5. Suspicious keywords in path or domain
        found_keywords = [kw for kw in self.SUSPICIOUS_KEYWORDS if kw in path or kw in domain]
        
        # 6. Special characters
        special_chars_count = {
            "@": url.count("@"),
            "-": domain.count("-"),
            "//": url[8:].count("//"),  # Count double slashes after the protocol
            "=": url.count("=")
        }
        
        # 7. TLD risk level
        tld_match = re.search(r"(\.[a-z]+)$", clean_domain)
        tld = tld_match.group(1) if tld_match else ""
        is_risky_tld = tld in self.RISKY_TLDS
        
        # 8. Domain age (mock WHOIS data)
        # In a real scenario, use python-whois string parsing. Here we mock it as 0 since we don't know
        mock_domain_age_days = 30 if is_risky_tld else 365 
        
        return {
            "length": length,
            "num_subdomains": num_subdomains,
            "has_ip": has_ip,
            "has_https": has_https,
            "suspicious_keywords": found_keywords,
            "special_chars": special_chars_count,
            "is_risky_tld": is_risky_tld,
            "domain_age_days": mock_domain_age_days
        }

    def _simulate_ml_classifier(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate an ML Classifier using weighted heuristics on features."""
        score = 0.0
        
        # Penalize IP address
        if features["has_ip"]:
            score += 0.4
            
        # Penalize lack of HTTPS
        if not features["has_https"]:
            score += 0.2
            
        # Penalize risky TLD
        if features["is_risky_tld"]:
            score += 0.3
            
        # Penalize long URLs
        if features["length"] > 75:
            score += 0.1
            
        # Penalize numerous subdomains
        if features["num_subdomains"] > 2:
            score += 0.2
            
        # Penalize suspicious keywords
        score += min(0.3, len(features["suspicious_keywords"]) * 0.15)
        
        # Map score to probability (0 to 1)
        ml_score = min(1.0, score)
        label = "phishing" if ml_score > 0.6 else "legitimate"
        
        return {
            "ml_score": ml_score,
            "label": label
        }

    def analyze(self, url: str) -> Dict[str, Any]:
        """Run the full URL analysis pipeline."""
        # A. Extract Features
        features = self.extract_features(url)
        
        # B. VirusTotal Check
        virustotal_result = check_url_in_virustotal(url)
        
        # C. ML Classifier
        ml_prediction = self._simulate_ml_classifier(features)
        
        # D. Combined URL Risk Score
        # Strategy: Rely primarily on VirusTotal. ML heuristics play a very minor fallback role.
        if virustotal_result["virustotal_match"]:
            url_risk_score = 1.0
        else:
            url_risk_score = ml_prediction["ml_score"] * 0.3  # Severely penalty to heuristic ML score
            
        # E. Formulate Explanation
        reasons = []
        if features["has_ip"]:
            reasons.append("uses an IP address instead of a domain name")
        if not features["has_https"]:
            reasons.append("lacks secure HTTPS encryption")
        if features["is_risky_tld"]:
            reasons.append("uses a high-risk top-level domain")
        if features["suspicious_keywords"]:
            reasons.append(f"contains suspicious keywords ({', '.join(features['suspicious_keywords'])})")
        if virustotal_result["virustotal_match"]:
            reasons.append("was flagged by security vendors on VirusTotal")
            
        explanation = "The URL is safe."
        if reasons:
            explanation = "The URL is suspicious because it " + ", and ".join(reasons) + "."
            
        return {
            "url": url,
            "features": features,
            "virustotal": virustotal_result,
            "ml_prediction": ml_prediction,
            "url_risk_score": url_risk_score,
            "explanation": explanation
        }
