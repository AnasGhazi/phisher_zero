from typing import Dict, Any
from config import settings

class EnsembleAgent:
    """Aggregates multiple agent scores using weighted logic."""
    
    def __init__(self):
        self.url_weight = settings.URL_WEIGHT
        self.nlp_weight = settings.NLP_WEIGHT
        self.virustotal_weight = settings.VIRUSTOTAL_WEIGHT
        self.threshold = settings.PHISHING_THRESHOLD
        self.suspicious_threshold = settings.SUSPICIOUS_THRESHOLD

    def aggregate(self, nlp_score: float, url_score: float = None, virustotal_confidence: float = 0.0) -> Dict[str, Any]:
        """
        Calculates the final confidence score based on individual agent scores.
        """
        if url_score is None:
            url_contrib = 0.0
            vt_contrib = 0.0
            nlp_contrib = nlp_score * 1.0  # 100% weight to NLP if no URL
            url_weight_used = 0.0
            nlp_weight_used = 1.0
            vt_weight_used = 0.0
        else:
            url_contrib = url_score * self.url_weight
            nlp_contrib = nlp_score * self.nlp_weight
            vt_contrib = virustotal_confidence * self.virustotal_weight
            url_weight_used = self.url_weight
            nlp_weight_used = self.nlp_weight
            vt_weight_used = self.virustotal_weight
            
        final_score = url_contrib + nlp_contrib + vt_contrib
        
        # Hard Override: If URL is provided and VirusTotal is highly confident, force phishing.
        if url_score is not None and virustotal_confidence >= 0.9:
            final_score = 1.0
            
        # Ensure it stays within bounds
        final_score = min(1.0, max(0.0, final_score))
            
        verdict = "phishing" if final_score >= self.threshold else ("suspicious" if final_score >= self.suspicious_threshold else "safe")
        
        if verdict == "phishing":
            explanation = "High risk detected across analyzed vectors."
        elif verdict == "suspicious":
            explanation = "Moderate indicators of phishing; exercise caution."
        else:
            explanation = "No significant phishing indicators found."
        
        return {
            "final_score": final_score,
            "verdict": verdict,
            "confidence": final_score if verdict == "phishing" else (1.0 - final_score),
            "contributions": {
                "url_agent": url_weight_used,
                "nlp_agent": nlp_weight_used,
                "virustotal": vt_weight_used
            },
            "explanation": explanation
        }
