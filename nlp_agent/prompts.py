# nlp_agent/prompts.py

FEW_SHOT = """
Example 1:
Email:
Subject: "Reset your password now"
Body: "We detected suspicious activity. Reset here: http://fake.example/reset"
JSON:
{{"is_phishing": 1, "reason": "Urgent reset link and suspicious domain not matching sender."}}

Example 2:
Email:
Subject: "Monthly newsletter"
Body: "Here is our monthly update..."
JSON:
{{"is_phishing": 0, "reason": "Generic newsletter language, no credential requests or suspicious links."}}
"""

PROMPT = FEW_SHOT + """
Now analyze the email below and respond with EXACTLY one JSON object (no explanation, no code fences).

Email:
Subject: {subject}
Body: {body}

Return JSON:
{{"is_phishing": <0 or 1>, "reason": "<short explanation>"}}
"""
