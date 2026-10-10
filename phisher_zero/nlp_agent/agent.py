import os
import json
import re
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_google_genai import ChatGoogleGenerativeAI
from .prompts import PROMPT, EMAIL_WORKFLOW_PROMPT
from .schemas import PhishResult

# --- Load environment variables ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if not API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY not found. Please set it in your .env file.")

# --- Initialize Gemini model ---
llm = ChatGoogleGenerativeAI(
    api_key=API_KEY,
    model=MODEL,
    temperature=0.0,
    max_output_tokens=400
)

# --- Build prompt and output parser ---
# Allow selecting which prompt template to use via env var `PROMPT_NAME`.
# Supported values: 'EMAIL_WORKFLOW_PROMPT' or 'PROMPT'. Defaults to EMAIL_WORKFLOW_PROMPT.
PROMPT_NAME = os.getenv("PROMPT_NAME", "EMAIL_WORKFLOW_PROMPT")
if PROMPT_NAME == "PROMPT":
    prompt_text = PROMPT
else:
    # prefer EMAIL_WORKFLOW_PROMPT; fall back to PROMPT if missing
    prompt_text = EMAIL_WORKFLOW_PROMPT if EMAIL_WORKFLOW_PROMPT else PROMPT

prompt_template = PromptTemplate(
    input_variables=["subject", "body"],
    template=prompt_text
)
parser = StrOutputParser()

# Combine components using the Runnable API
chain = RunnableSequence(prompt_template | llm | parser)

# --- JSON extraction regex ---
JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

def parse_json_from_text(text: str):
    """Extract first {...} block from LLM text and parse JSON."""
    match = JSON_RE.search(text)
    if not match:
        raise ValueError("No JSON object found in LLM output")
    raw = match.group()
    return json.loads(raw)

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

try:
    # Load model and tokenizer
    # Using the pre-trained model specified by the user
    hf_model_name = "cybersectony/phishing-email-detection-distilbert_v2.4.1"
    hf_tokenizer = AutoTokenizer.from_pretrained(hf_model_name)
    hf_model = AutoModelForSequenceClassification.from_pretrained(hf_model_name)
except Exception as e:
    print(f"[!] Warning: Could not load Hugging Face model: {e}")
    hf_tokenizer = None
    hf_model = None

class NLPAgent:
    def analyze_email(self, email_text: str) -> PhishResult:
        """Original analyze_email using Gemini API."""
        # Simple subject/body split
        subject, body = self._extract_subject_body(email_text)

        try:
            resp = chain.invoke({"subject": subject or "", "body": body or ""})
        except Exception as e:
            return PhishResult(is_phishing=1, reason=f"LLM invocation error: {e}")

        try:
            parsed = parse_json_from_text(resp)
            is_phish = int(parsed.get("is_phishing", 0))
            reason = str(parsed.get("reason", "")).strip()

            if is_phish not in (0, 1):
                is_phish = 1 if float(parsed.get("is_phishing", 0)) > 0.5 else 0

            return PhishResult(is_phishing=is_phish, reason=reason)
        except Exception as e:
            return PhishResult(
                is_phishing=1,
                reason=f"⚠️ Parsing failed: {e}. Raw LLM output: {str(resp)[:300]}"
            )

    def analyze_with_hf(self, email_text: str) -> dict:
        """
        Analyze email using the Hugging Face BERT model.
        Returns a dict with 'prediction', 'confidence', etc.
        """
        if not hf_model or not hf_tokenizer:
            return {"prediction": "unknown", "confidence": 0.0, "error": "Model not loaded"}
            
        try:
            # Preprocess and tokenize
            inputs = hf_tokenizer(
                email_text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            # Get prediction
            with torch.no_grad():
                outputs = hf_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Get probabilities for each class
            probs = predictions[0].tolist()
            
            # Create labels dictionary
            labels = {
                "legitimate_email": probs[0],
                "phishing_url": probs[1],
                "legitimate_url": probs[2],
                "phishing_url_alt": probs[3]
            }
            
            # Determine the most likely classification
            max_label = max(labels.items(), key=lambda x: x[1])
            
            return {
                "prediction": max_label[0],
                "confidence": max_label[1],
                "all_probabilities": labels,
                "nlp_score": 1.0 - probs[0]  # Score is 1.0 minus legitimate probability
            }
        except Exception as e:
            return {"prediction": "error", "confidence": 0.0, "error": str(e), "nlp_score": 0.5}

    def get_score(self, email_text: str) -> float:
        """
        Returns a normalized nlp_score between 0 and 1 for the Ensemble Agent.
        Uses the Hugging Face model if available, falling back to Gemini text extraction.
        """
        if hf_model:
            result = self.analyze_with_hf(email_text)
            return result.get("nlp_score", 0.0)
        else:
            # Fall back to the original method
            result = self.analyze_email(email_text)
            return float(result.is_phishing)

    def _extract_subject_body(self, email_text: str):
        lines = email_text.split("\n", 1)
        subject = lines[0] if lines else ""
        body = lines[1] if len(lines) > 1 else ""
        return subject, body
