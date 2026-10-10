import json
import logging
import google.generativeai as genai
from typing import Dict, Any
from config import settings

logger = logging.getLogger(__name__)

class ExplainerAgent:
    """Agent that translates technical signals into user-friendly explanations using LLM."""
    
    SYSTEM_PROMPT = """You are a cybersecurity assistant.

Based ONLY on the structured analysis below, explain why this email or URL is classified as phishing or safe.

DATA:
{json_input}

INSTRUCTIONS:
- Do not add assumptions
- Do not invent facts
- Use only given signals
- Return ONLY valid JSON format. No markdown blocks, no extra text.

OUTPUT FORMAT MUST BE EXACTLY THIS JSON STRUCTURE:
{{
  "summary": "<1-2 lines summarizing the verdict>",
  "key_reasons": ["<reason 1>", "<reason 2>"],
  "risk_level": "<Low/Medium/High>",
  "recommended_action": "<1 line action>"
}}"""

    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        # Fall back to stripping quotes if they are accidentally included in .env
        if self.api_key:
            self.api_key = self.api_key.strip("'").strip('"')
            
        self.model_name = settings.GEMINI_MODEL
        
        self.is_configured = False
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.is_configured = True
            except Exception as e:
                logger.error(f"Failed to configure Gemini for Explainer: {e}")
        else:
            logger.warning("GOOGLE_API_KEY not found. ExplainerAgent will use fallback logic.")

    def explain(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explanation, falling back to rule-based if LLM fails or is unconfigured."""
        if self.is_configured:
            try:
                return self._generate_llm_explanation(analysis_data)
            except Exception as e:
                logger.error(f"LLM explanation failed: {e}. Using fallback.")
                return self._generate_fallback_explanation(analysis_data)
        else:
            return self._generate_fallback_explanation(analysis_data)

    def _generate_llm_explanation(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.SYSTEM_PROMPT.format(json_input=json.dumps(analysis_data, indent=2))
        
        response = self.model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        
        try:
            parsed = json.loads(text)
            # Ensure required keys exist
            required_keys = ["summary", "key_reasons", "risk_level", "recommended_action"]
            for k in required_keys:
                if k not in parsed:
                    raise ValueError(f"Missing key in LLM output: {k}")
            return parsed
        except Exception as e:
            logger.error(f"Failed to parse LLM explanation JSON: {e}\nRaw Text: {text}")
            raise

    def _generate_fallback_explanation(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based fallback explanation maker."""
        verdict = analysis_data.get("verdict", "safe")
        url_agent = analysis_data.get("url_agent") or {}
        nlp_agent = analysis_data.get("nlp_agent") or {}
        
        reasons = []
        
        if "virustotal" in url_agent and url_agent["virustotal"].get("virustotal_match"):
            reasons.append("The exact URL is listed in VirusTotal's database of known threats by security vendors.")
            
        if url_agent.get("ml_prediction", {}).get("label") == "phishing":
            reasons.append("URL structural features tightly map to generic phishing patterns.")
            
        nlp_score = nlp_agent.get("nlp_score", 0.0)
        if isinstance(nlp_score, (int, float)) and nlp_score > 0.7:
            reasons.append("The text heavily utilizes suspicious semantic patterns like urgency or credentials requests.")

        if verdict == "phishing":
            summary = "This content has been flagged as phishing due to strong malicious indicators."
            risk_level = "High"
            recommended_action = "Do not interact with the content, do not click links, and report it immediately."
            if not reasons: reasons.append("Multiple indicators crossed the threshold for a phishing categorization.")
        elif verdict == "suspicious":
            summary = "This content appears suspicious and contains some risky elements."
            risk_level = "Medium"
            recommended_action = "Proceed with caution. Verify the sender/URL via an independent channel before proceeding."
            if not reasons: reasons.append("Some minor indicators suggest it might not be legitimate.")
        else:
            summary = "We did not find any prominent indicators of phishing."
            risk_level = "Low"
            recommended_action = "Safe to proceed, but always maintain standard security awareness."
            reasons = ["No malicious elements were triggered during analysis."]
            
        return {
            "summary": summary,
            "key_reasons": reasons,
            "risk_level": risk_level,
            "recommended_action": recommended_action
        }
