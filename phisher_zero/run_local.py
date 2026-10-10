# run_local.py
import importlib
import inspect
import json
import os
from dotenv import load_dotenv

load_dotenv()  # loads GEMINI_API_KEY or GOOGLE_API_KEY from .env if present

MODULE_PATH = "nlp_agent.agent"
SAMPLE_EMAILS = [
    "Dear user, your account has been compromised. Click here to reset: http://fakebank-login.com",
    "Team — Reminder: monthly meeting tomorrow at 2pm. Agenda attached.",
    "Hello, you won a prize! Verify your identity by providing your account password."
]

def find_agent_class(module):
    """
    Find a class in module that has an 'analyze_email' method.
    Return the class object or None.
    """
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # only classes defined in that module (not imported)
        if obj.__module__ != module.__name__:
            continue
        if hasattr(obj, "analyze_email") and callable(getattr(obj, "analyze_email")):
            return obj
    return None

def main():
    print("▶ run_local.py — starting")
    try:
        mod = importlib.import_module(MODULE_PATH)
    except Exception as e:
        print(f"✖ Failed to import `{MODULE_PATH}`: {e}")
        return

    AgentClass = find_agent_class(mod)
    if not AgentClass:
        print("✖ Could not find an agent class with an `analyze_email(self, email_text)` method in", MODULE_PATH)
        print("  Inspect nlp_agent/agent.py and ensure there is a class with a method named `analyze_email`.")
        return

    print(f"ℹ Found agent class: {AgentClass.__name__}")

    # try to instantiate (no args). If your agent needs args, modify here.
    try:
        agent = AgentClass()
    except TypeError as e:
        print(f"✖ Failed to instantiate {AgentClass.__name__} without args: {e}")
        print("  If your agent requires init args, update run_local.py to pass them.")
        return
    except Exception as e:
        print(f"✖ Error during instantiation of {AgentClass.__name__}: {e}")
        return

    # sanity check: ensure method exists
    if not hasattr(agent, "analyze_email") or not callable(getattr(agent, "analyze_email")):
        print("✖ The instantiated object does not have a callable analyze_email method.")
        return

    print("✅ Agent instantiated. Running sample emails...\n")

    for i, email in enumerate(SAMPLE_EMAILS, 1):
        try:
            out = agent.analyze_email(email)
            # If agent returns a pydantic model or dict-like, try to normalize to dict
            if hasattr(out, "model_dump"):
                normalized = out.model_dump()
            elif hasattr(out, "dict"):
                normalized = out.dict()
            elif isinstance(out, dict):
                normalized = out
            else:
                # it's likely a string (raw LLM output)
                normalized = {"raw": str(out)}
        except Exception as e:
            normalized = {"error": str(e)}

        print(f"--- Sample #{i} ---")
        print("Email:", email)
        print("Result:", json.dumps(normalized, indent=2, ensure_ascii=False))
        print()

    print("▶ done.")

if __name__ == "__main__":
    main()
