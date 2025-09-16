import re
import json
from typing import Dict, List, Tuple, Optional
from config import SENSITIVE_PATTERNS, CODE_PATTERNS, BUSINESS_PATTERNS, USE_SECURE_FILTER, SECURITY_LEVEL
import hashlib
import sys
sys.path.append('../ai_proxy_admin_dashboard')
from ai_proxy_admin_dashboard.sqlite_logger import log_masking_event
from ai_proxy_admin_dashboard.sqlite_logger import init_db
init_db()


class SmartMasker:
    def __init__(self, security_level: str = "high"):
        self.security_level = security_level
        self.masking_stats = {
            "pii_masked": 0,
            "code_detected": False,
            "business_content_detected": False,
            "sensitive_patterns_found": []
        }
        
    def detect_content_type(self, text: str) -> Dict[str, bool]:
        """Detect the type of content in the text"""
        content_types = {
            "code": False,
            "business_document": False,
            "technical_document": False,
            "personal_data": False
        }
        
        # Detect code content
        code_score = 0
        for pattern_list in CODE_PATTERNS.values():
            for pattern in pattern_list:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    code_score += 1
        
        if code_score >= 3:
            content_types["code"] = True
            self.masking_stats["code_detected"] = True
        
        # Detect business content
        business_score = 0
        for pattern_list in BUSINESS_PATTERNS.values():
            for pattern in pattern_list:
                if re.search(pattern, text, re.IGNORECASE):
                    business_score += 1
        
        if business_score >= 2:
            content_types["business_document"] = True
            self.masking_stats["business_content_detected"] = True
        
        # Detect technical documentation
        tech_terms = ["api", "endpoint", "database", "server", "client", "protocol", "interface"]
        tech_score = sum(1 for term in tech_terms if re.search(rf"\b{term}\b", text, re.IGNORECASE))
        if tech_score >= 3:
            content_types["technical_document"] = True
        
        return content_types
    
    def mask_sensitive_patterns(self, text: str) -> str:
        """Mask sensitive patterns while preserving context"""
        masked_text = text
        
        for category, patterns in SENSITIVE_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, masked_text, re.IGNORECASE)
                for match in matches:
                    original = match.group(0)
                    # Create context-aware replacement
                    if category == "api_keys":
                        replacement = "<API_KEY>"
                    elif category == "passwords":
                        replacement = "<PASSWORD>"
                    elif category == "urls":
                        replacement = "<URL>"
                    elif category == "ips":
                        replacement = "<IP_ADDRESS>"
                    elif category == "paths":
                        replacement = "<FILE_PATH>"
                    elif category == "emails":
                        replacement = "<EMAIL>"
                    elif category == "phone_numbers":
                        replacement = "<PHONE>"
                    elif category == "credit_cards":
                        replacement = "<CREDIT_CARD>"
                    elif category == "ssn":
                        replacement = "<SSN>"
                    else:
                        replacement = f"<{category.upper()}>"
                    
                    masked_text = masked_text.replace(original, replacement)
                    self.masking_stats["pii_masked"] += 1
                    self.masking_stats["sensitive_patterns_found"].append(category)
        
        return masked_text
    # # Example masking stats from your masking logic
    # masking_stats = {
    #     "sensitive_patterns_found": ["api_keys", "email", "email", "password"],
    #     # ... other stats
    # }

    # # Generate a user hash (e.g., from session, IP, or random for demo)
    # import hashlib
    # user_id = "user@example.com"  # Or session ID, or IP, or random string
    # user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]  # Only store the hash

    # file_type = "py"  # or extract from filename

    # entry = {
    #     "user_hash": user_hash,
    #     "status": "masked",
    #     "file_type": file_type,
    #     "masked_types": list(set(masking_stats["sensitive_patterns_found"])),
    #     "masked_type_count": {t: masking_stats["sensitive_patterns_found"].count(t) for t in set(masking_stats["sensitive_patterns_found"])}
    # }

    # append_log(entry)


    def mask_code_content(self, text: str) -> str:
        """Intelligently mask code while preserving structure and logic"""
        masked_text = text
        
        # Mask import statements and dependencies
        import_patterns = [
            r"^(import|from|using|require|include)\s+[^\n]+",
            r"^\s*(import|from|using|require|include)\s+[^\n]+"
        ]
        
        for pattern in import_patterns:
            masked_text = re.sub(pattern, "<IMPORT_STATEMENT>", masked_text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Mask file paths in code
        file_path_patterns = [
            r"['\"][^'\"]*\.(py|js|ts|java|cpp|c|cs|php|rb|go|rs|swift|kt|scala|r|m|pl|sh|bash|ps1|vbs|sql|html|css|xml|json|yaml|yml|toml|ini|cfg|conf|config)['\"]",
            r"['\"][^'\"]*/(?:[^/\n]+/)*[^/\n]*['\"]",
            r"['\"][^'\"]*[A-Za-z]:\\(?:[^\\\n]+\\)*[^\\\n]*['\"]"
        ]
        
        for pattern in file_path_patterns:
            masked_text = re.sub(pattern, '"<FILE_PATH>"', masked_text)
        
        # Mask configuration values
        config_patterns = [
            r"(\w+)\s*[:=]\s*['\"][^'\"]+['\"]",  # key: "value" or key = "value"
            r"(\w+)\s*[:=]\s*\d+",  # key: 123 or key = 123
        ]
        
        for pattern in config_patterns:
            masked_text = re.sub(pattern, r"\1 = <CONFIG_VALUE>", masked_text)
        
        return masked_text
    
    def mask_business_content(self, text: str) -> str:
        """Mask business-sensitive content while preserving document structure"""
        masked_text = text
        
        # Mask company names and identifiers
        company_patterns = [
            r"\b[A-Z]{2,}(?:[A-Z][a-z]+)*\s+(?:Inc|Corp|LLC|Ltd|Company|Corporation)\b",
            r"\b(?:company|organization|enterprise|business)\s+[A-Z][a-z]+\b",
        ]
        
        for pattern in company_patterns:
            masked_text = re.sub(pattern, "<COMPANY_NAME>", masked_text, flags=re.IGNORECASE)
        
        # Mask financial information
        financial_patterns = [
            r"\$\d+(?:,\d{3})*(?:\.\d{2})?",  # Currency amounts
            r"\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|EUR|GBP)\b",
            r"\b(?:revenue|profit|margin|cost|budget)\s*[:=]\s*[\$]?\d+",
        ]
        
        for pattern in financial_patterns:
            masked_text = re.sub(pattern, "<FINANCIAL_AMOUNT>", masked_text, flags=re.IGNORECASE)
        
        # Mask project and initiative names
        project_patterns = [
            r"\b(?:project|initiative|strategy|roadmap)\s+[A-Z][a-zA-Z\s]+",
            r"\b[A-Z][a-zA-Z\s]{3,}(?:Project|Initiative|Strategy|Roadmap)\b",
        ]
        
        for pattern in project_patterns:
            masked_text = re.sub(pattern, "<PROJECT_NAME>", masked_text, flags=re.IGNORECASE)
        
        return masked_text
    
    def extract_context_clues(self, text: str, content_types: Dict[str, bool]) -> List[str]:
        """Extract context clues to help the AI understand the masked content"""
        clues = []
        
        # Extract comments and documentation
        comments = re.findall(r'#.*|//.*|/\*[\s\S]*?\*/|<!--[\s\S]*?-->', text)
        if comments:
            clues.append(f"Found {len(comments)} comment(s) that provide context about the code/document structure")
        
        # Extract function/class names (without revealing implementation)
        function_names = re.findall(r'\b(?:def|function|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)', text)
        if function_names:
            clues.append(f"Contains {len(function_names)} function/class definition(s): {', '.join(function_names[:3])}")
        
        # Extract file extensions mentioned
        extensions = re.findall(r'\.(py|js|ts|java|cpp|c|cs|php|rb|go|rs|swift|kt|scala|r|m|pl|sh|bash|ps1|vbs|sql|html|css|xml|json|yaml|yml|toml|ini|cfg|conf|config)\b', text)
        if extensions:
            clues.append(f"References file types: {', '.join(set(extensions))}")
        
        # Extract programming language indicators
        lang_indicators = {
            "python": ["import", "def", "class", "if __name__", "self."],
            "javascript": ["function", "const", "let", "var", "=>", "console.log"],
            "java": ["public class", "public static", "import java", "System.out"],
            "sql": ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE TABLE"],
        }
        
        for lang, indicators in lang_indicators.items():
            if any(indicator in text for indicator in indicators):
                clues.append(f"Appears to be {lang} code")
                break
        
        return clues
    
    def generate_ai_prompt(self, content_types: Dict[str, bool], clues: List[str], masking_stats: Dict) -> str:
        """Generate an AI-friendly prompt that explains the masking and provides context"""
        prompt_parts = []
        
        prompt_parts.append("🔒 SECURITY NOTICE: This content has been automatically redacted to protect sensitive information.")
        
        if content_types["code"]:
            prompt_parts.append("📝 CONTENT TYPE: Source code detected")
            prompt_parts.append("💡 ANALYSIS FOCUS: Code structure, logic flow, and architectural patterns")
        elif content_types["business_document"]:
            prompt_parts.append("📄 CONTENT TYPE: Business document detected")
            prompt_parts.append("💡 ANALYSIS FOCUS: Document structure, business logic, and process flows")
        elif content_types["technical_document"]:
            prompt_parts.append("🔧 CONTENT TYPE: Technical documentation detected")
            prompt_parts.append("💡 ANALYSIS FOCUS: Technical specifications and system architecture")
        
        if masking_stats["pii_masked"] > 0:
            prompt_parts.append(f"🛡️ SECURITY: {masking_stats['pii_masked']} sensitive elements masked")
        
        if clues:
            prompt_parts.append("🔍 CONTEXT CLUES:")
            for clue in clues:
                prompt_parts.append(f"  • {clue}")
        
        prompt_parts.append("\n📋 INSTRUCTIONS:")
        prompt_parts.append("• Analyze the structure and logic of the content")
        prompt_parts.append("• Provide insights about patterns and best practices")
        prompt_parts.append("• Suggest improvements or identify potential issues")
        prompt_parts.append("• Focus on the overall architecture and design principles")
        
        prompt_parts.append("\n" + "="*50 + "\n")
        
        return "\n".join(prompt_parts)

def smart_mask(text: str, file_name: str = "", use_secure_filter: bool = None) -> Tuple[str, str]:
    """
    Enhanced smart masking function that filters PII, source code, and business secrets
    while maintaining context and accuracy.
    
    Args:
        text: Input text to mask
        file_name: Name of the file (for context)
        use_secure_filter: Override the global setting
    
    Returns:
        Tuple of (masked_text, ai_prompt)
    """
    if use_secure_filter is None:
        use_secure_filter = USE_SECURE_FILTER
    
    # If secure filtering is disabled, return original text with minimal processing
    if not use_secure_filter:
        return text, "🔓 PERSONAL MODE: Content is being processed without security filtering.\n\n"
    
    masker = SmartMasker(SECURITY_LEVEL)
    
    # Detect content type
    content_types = masker.detect_content_type(text)
    
    # Apply masking based on content type and security level
    masked_text = text
    
    # Always mask sensitive patterns
    masked_text = masker.mask_sensitive_patterns(masked_text)
    
    # Apply content-specific masking
    if content_types["code"]:
        masked_text = masker.mask_code_content(masked_text)
    
    if content_types["business_document"]:
        masked_text = masker.mask_business_content(masked_text)
    
    # Extract context clues
    clues = masker.extract_context_clues(text, content_types)
    
    # Generate AI prompt
    ai_prompt = masker.generate_ai_prompt(content_types, clues, masker.masking_stats)
    
    #logging the masked text
    user_id = "user@example.com"  # Replace with session, IP, or random for real use
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    file_type = file_name.split('.')[-1] if '.' in file_name else "txt"
    # Log each masked type and its count to SQLite
    masked_type_counts = {t: masker.masking_stats["sensitive_patterns_found"].count(t) for t in set(masker.masking_stats["sensitive_patterns_found"])}
    for masked_type, count in masked_type_counts.items():
        log_masking_event(masked_type, file_type, count)
    return masked_text, ai_prompt
    


def get_masking_stats() -> Dict:
    """Get statistics about the last masking operation"""
    # This would need to be implemented as a class method or global state
    # For now, return a placeholder
    return {
        "pii_masked": 0,
        "code_detected": False,
        "business_content_detected": False,
        "sensitive_patterns_found": []
    } 