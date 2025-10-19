import os
import json
import re
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_google_genai import ChatGoogleGenerativeAI
from .prompts import PROMPT
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
prompt_template = PromptTemplate(
    input_variables=["subject", "body"],
    template=PROMPT
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

class NLPAgent:
    def analyze_email(self, email_text: str) -> PhishResult:
        """Analyze an email text (single string) and return PhishResult."""
        # Simple subject/body split for demo purposes
        subject, body = self._extract_subject_body(email_text)

        # Use the RunnableSequence invoke() method (not .run())
        # Provide a mapping of input variables expected by the PromptTemplate
        try:
            resp = chain.invoke({"subject": subject or "", "body": body or ""})
        except Exception as e:
            return PhishResult(is_phishing=1, reason=f"LLM invocation error: {e}")

        # resp should be a string (the model output). Parse JSON inside it.
        try:
            parsed = parse_json_from_text(resp)
            is_phish = int(parsed.get("is_phishing", 0))
            reason = str(parsed.get("reason", "")).strip()

            # Coerce to 0/1
            if is_phish not in (0, 1):
                is_phish = 1 if float(parsed.get("is_phishing", 0)) > 0.5 else 0

            return PhishResult(is_phishing=is_phish, reason=reason)

        except Exception as e:
            return PhishResult(
                is_phishing=1,
                reason=f"⚠️ Parsing failed: {e}. Raw LLM output: {str(resp)[:300]}"
            )

    def _extract_subject_body(self, email_text: str):
        """Naive subject/body extractor: first line -> subject, rest -> body."""
        lines = email_text.split("\n", 1)
        subject = lines[0] if lines else ""
        body = lines[1] if len(lines) > 1 else ""
        return subject, body
