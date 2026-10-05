"""Core logic: static pre-checks (Python AST) + Groq LLM call + JSON validation."""
import ast, json, os, re
import prompts

MODEL = "openai/gpt-oss-120b"
SECRET_RE = re.compile(r"(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{6,}['\"]", re.I)


def static_check(code: str, language: str) -> list[dict]:
    """Cheap deterministic checks that run BEFORE the LLM and are passed to it as evidence."""
    findings = []
    if language.lower() == "python":
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [{"line": e.lineno, "type": "syntax_error", "message": e.msg}]
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                findings.append({"line": node.lineno, "type": "bare_except", "message": "Bare 'except:' hides errors"})
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                findings.append({"line": node.lineno, "type": "dangerous_call", "message": f"Use of {node.func.id}()"})
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for d in node.args.defaults:
                    if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                        findings.append({"line": node.lineno, "type": "mutable_default", "message": f"Mutable default argument in {node.name}()"})
    for i, line in enumerate(code.splitlines(), 1):
        if SECRET_RE.search(line):
            findings.append({"line": i, "type": "hardcoded_secret", "message": "Possible hardcoded credential"})
    return findings


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


def analyze(api_key: str, mode: str, code: str, language: str, error: str = "") -> dict:
    from groq import Groq  # imported lazily so static checks work without the package
    static = static_check(code, language)
    user = (f"Language: {language}\n\nCODE:\n{code}\n\n"
            f"ERROR MESSAGE (may be empty):\n{error or 'None'}\n\n"
            f"STATIC ANALYSIS EVIDENCE (deterministic, trust it):\n{json.dumps(static)}")
    client = Groq(api_key=api_key)
    last_err = None
    for _ in range(2):  # one retry if the model returns malformed JSON
        resp = client.chat.completions.create(
            model=MODEL, temperature=0.1,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": prompts.build_system_prompt(mode)},
                      {"role": "user", "content": user}])
        try:
            return {"static": static, "result": _parse_json(resp.choices[0].message.content)}
        except json.JSONDecodeError as e:
            last_err = e
    raise ValueError(f"Model returned invalid JSON: {last_err}")


def to_markdown(mode: str, language: str, data: dict) -> str:
    """Build the downloadable report."""
    out = [f"# CodePilot AI Report - {mode}", f"Language: {language}", ""]
    if data["static"]:
        out += ["## Static analysis"] + [f"- line {f['line']}: {f['message']}" for f in data["static"]] + [""]
    for key, val in data["result"].items():
        out.append(f"## {key.replace('_', ' ').title()}")
        if key.endswith("code"):
            out += [f"```{language.lower()}", str(val), "```"]
        elif isinstance(val, list):
            out += [f"- {json.dumps(v) if isinstance(v, dict) else v}" for v in val]
        else:
            out.append(str(val))
        out.append("")
    return "\n".join(out)
