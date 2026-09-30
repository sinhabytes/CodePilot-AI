"""Specialised prompts for CodePilot AI. Each mode = one prompt + one JSON schema."""

BASE = (
    "You are a senior software engineer doing a careful code analysis. "
    "Only report problems that really exist in the given code - never invent issues. "
    "Do not change unrelated parts of the code. "
    "Respond with ONE valid JSON object and nothing else (no markdown fences)."
)

MODES = {
    "Full Code Review": {
        "task": "Review the code for bugs, security issues, performance problems and code quality.",
        "schema": '{"quality_score": <0-100 integer>, "summary": "<2 sentences>", '
                  '"bugs": [{"line": "<line or function>", "issue": "", "fix": ""}], '
                  '"security_issues": [{"severity": "low|medium|high", "issue": "", "fix": ""}], '
                  '"performance": ["<suggestion>"], "code_quality": ["<issue>"], '
                  '"suggestions": ["<improvement>"], "improved_code": "<full corrected code>"}',
    },
    "Debug an Error": {
        "task": "Analyse the code and the error message. Find the probable cause, the exact "
                "problematic section, why the error occurs, and provide corrected code.",
        "schema": '{"probable_cause": "", "problem_section": "", "why_it_happens": "", '
                  '"corrected_code": "<full corrected code>", "explanation_of_fix": ""}',
    },
    "Security Audit": {
        "task": "Audit the code for hardcoded credentials, unsafe input handling, SQL injection, "
                "dangerous file/OS operations, insecure API usage and similar weaknesses.",
        "schema": '{"risk_level": "low|medium|high|none", "findings": [{"severity": "low|medium|high", '
                  '"category": "", "issue": "", "fix": ""}], "secure_code": "<full hardened code>"}',
    },
    "Generate Test Cases": {
        "task": "Generate test cases for the code: normal, edge, invalid-input and boundary cases.",
        "schema": '{"normal_cases": [{"input": "", "expected": ""}], "edge_cases": [{"input": "", "expected": ""}], '
                  '"invalid_inputs": [{"input": "", "expected": ""}], "boundary_cases": [{"input": "", "expected": ""}], '
                  '"test_code": "<runnable unit tests in the same language>"}',
    },
    "Explain Code": {
        "task": "Explain the code in a beginner-friendly way, step by step.",
        "schema": '{"overview": "", "step_by_step": ["<explanation of each part>"], '
                  '"key_concepts": ["<concept>"], "complexity": "<time/space complexity if relevant>"}',
    },
}

def build_system_prompt(mode: str) -> str:
    m = MODES[mode]
    return f"{BASE}\n\nTASK: {m['task']}\n\nReturn JSON exactly in this shape:\n{m['schema']}"
