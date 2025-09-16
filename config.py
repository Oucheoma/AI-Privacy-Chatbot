import os

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "missing-api-key")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Debug: Print the API key value
print("OPENROUTER_API_KEY loaded:", OPENROUTER_API_KEY)

# Temporary fix: Hardcode the API key for testing
if not OPENROUTER_API_KEY:
    OPENROUTER_API_KEY = "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"
    print("Using hardcoded API key for testing")

# Security Configuration
USE_SECURE_FILTER = os.getenv("USE_SECURE_FILTER", "True").lower() == "true"
SECURITY_LEVEL = os.getenv("SECURITY_LEVEL", "high")  # low, medium, high

# Enhanced filtering patterns
SENSITIVE_PATTERNS = {
    "api_keys": [
        r"(api_key|api_key_|token|access_token|secret_key|private_key)[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9_\-]{16,}[\"']?",
        r"sk-[a-zA-Z0-9]{48}",
        r"pk_[a-zA-Z0-9]{48}",
        r"[a-zA-Z0-9]{32,}",
        # add more regex paettrn
        # ner
    ],
    "passwords": [
        r"(password|passwd|pwd)[\"']?\s*[:=]\s*[\"']?[^\s\"']+[\"']?",
        r"password\s*=\s*['\"][^'\"]+['\"]",
    ],
    "urls": [
        r"https?://[^\s\"']+",
        r"ftp://[^\s\"']+",
        r"ssh://[^\s\"']+",
    ],
    "ips": [
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        r"localhost",
        r"127\.0\.0\.1",
    ],
    "paths": [
        r"/(?:[^/\n]+/)*[^/\n]*",
        r"[A-Za-z]:\\(?:[^\\\n]+\\)*[^\\\n]*",
        r"~/[^/\n]*",
    ],
    "emails": [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    ],
    "phone_numbers": [
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        r"\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b",
        r"\(\d{3}\)\s*\d{3}[-.]?\d{4}",
    ],
    "names": [
        # Enhanced name patterns that are more flexible
        r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # First Last
        r"\b[A-Z][a-z]+\s+[A-Z]\.\s*[A-Z][a-z]+\b",  # First M. Last
        r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # First Middle Last
        r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z]\.\b",  # First Last M.
        r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # First Middle Middle Last
    ],
    "companies": [
        r"\b[A-Z]{2,}(?:[A-Z][a-z]+)*\s+(?:Inc|Corp|LLC|Ltd|Company|Corporation|Limited|Partnership|Associates)\b",
        r"\b(?:company|organization|enterprise|business)\s+[A-Z][a-z]+\b",
        r"\b[A-Z][a-z]+\s+(?:Technologies|Systems|Solutions|Services|Group|Industries|International|Global)\b",
    ],
    "addresses": [
        r"\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Place|Pl|Way|Terrace|Ter)\b",
        r"\d+\s+[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b",
    ],
    "credit_cards": [
        r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    ],
    "ssn": [
        r"\b\d{3}-\d{2}-\d{4}\b",
        r"\b\d{9}\b",
    ]
}

# Code and document detection patterns
CODE_PATTERNS = {
    "programming_keywords": [
        r"\b(function|def|class|import|export|require|include|package|namespace|module)\b",
        r"\b(if|else|for|while|switch|case|try|catch|finally|throw)\b",
        r"\b(var|let|const|int|string|boolean|float|double|void|return)\b",
        r"\b(public|private|protected|static|final|abstract|interface|extends|implements)\b",
    ],
    "file_extensions": [
        r"\.(py|js|ts|java|cpp|c|cs|php|rb|go|rs|swift|kt|scala|r|m|pl|sh|bash|ps1|vbs|sql|html|css|xml|json|yaml|yml|toml|ini|cfg|conf|config)$",
    ],
    "code_blocks": [
        r"```[\s\S]*?```",
        r"`[^`]+`",
    ],
    "import_statements": [
        r"^(import|from|using|require|include)\s+",
        r"^\s*(import|from|using|require|include)\s+",
    ]
}

# Business and confidential content patterns
BUSINESS_PATTERNS = {
    "confidential_terms": [
        r"\b(confidential|secret|private|internal|proprietary|classified|restricted)\b",
        r"\b(nda|non-disclosure|trade\s+secret|intellectual\s+property)\b",
        r"\b(revenue|profit|margin|cost|budget|financial|accounting|billing)\b",
        r"\b(employee|hr|human\s+resources|salary|compensation|benefits)\b",
        r"\b(customer|client|vendor|supplier|partner|stakeholder)\b",
        r"\b(project|initiative|strategy|roadmap|milestone|deadline)\b",
    ],
    "company_identifiers": [
        r"\b[A-Z]{2,}(?:[A-Z][a-z]+)*\s+(?:Inc|Corp|LLC|Ltd|Company|Corporation)\b",
        r"\b(?:company|organization|enterprise|business)\s+[A-Z][a-z]+\b",
    ],
    "document_types": [
        r"\b(contract|agreement|proposal|report|memo|brief|presentation|deck)\b",
        r"\b(manual|guide|documentation|specification|requirements|design)\b",
        r"\b(policy|procedure|process|workflow|standard|protocol)\b",
    ]
}
