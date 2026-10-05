import os
from collections.abc import Mapping

import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError
import analyzer, prompts

load_dotenv()
st.set_page_config(page_title="CodePilot AI", page_icon="🧑‍✈️", layout="wide")

try:
    secrets = st.secrets
except StreamlitSecretNotFoundError:
    secrets = {}

API_KEY = (os.getenv("GROQ_API_KEY", "") or secrets.get("GROQ_API_KEY", "")).strip()
if not API_KEY:
    groq_secrets = secrets.get("GROQ", {})
    if isinstance(groq_secrets, Mapping):
        API_KEY = str(groq_secrets.get("GROQ_API_KEY", "")).strip()
KEY_IS_PLACEHOLDER = any(
    marker in API_KEY.lower()
    for marker in ("your", "replace", "example", "placeholder", "paste")
)
LANGS = ["Python", "JavaScript", "Java", "C++", "C", "SQL", "Other"]
EXT = {"py": "Python", "js": "JavaScript", "java": "Java", "cpp": "C++", "c": "C", "sql": "SQL"}

st.title("🧑‍✈️ CodePilot AI")
st.caption("Intelligent Code Review & Debugging Assistant - Streamlit + Groq + Prompt Engineering")

with st.sidebar:
    st.header("Settings")
    mode = st.selectbox("Analysis type", list(prompts.MODES))
    language = st.selectbox("Language", LANGS)
    upload = st.file_uploader("...or upload a code file", type=list(EXT))
    st.divider()
    st.markdown("**Pipeline**\n\nInput → AST static checks → Specialised prompt → Groq LLM → JSON validation → Report")

default = ""
if upload:
    default = upload.read().decode("utf-8", errors="ignore")
    ext = upload.name.rsplit(".", 1)[-1].lower()
    language = EXT.get(ext, language)

code = st.text_area("Paste your code", value=default, height=300)
error = st.text_area("Error message (optional)", height=80) if mode == "Debug an Error" else ""

if st.button("Analyze Code", type="primary", use_container_width=True):
    if not API_KEY:
        st.error(
            "GROQ_API_KEY is missing. Add your replacement key to `.env` as "
            "`GROQ_API_KEY=your_key`, or to `.streamlit/secrets.toml` as "
            "`GROQ_API_KEY = \"your_key\"` (or under `[GROQ]`)."
        )
    elif KEY_IS_PLACEHOLDER:
        st.error(
            "GROQ_API_KEY still looks like a placeholder. Replace it in `.env` "
            "with the actual key from your Groq account, then refresh the app."
        )
    elif not code.strip():
        st.warning("Please paste or upload some code.")
    else:
        with st.spinner("Analyzing..."):
            try:
                st.session_state.data = analyzer.analyze(API_KEY, mode, code, language, error)
                st.session_state.meta = (mode, language)
            except Exception as e:
                st.error(f"Analysis failed: {e}")

def render(key, val):
    title = key.replace("_", " ").title()
    st.subheader(title)
    if key.endswith("code"):
        st.code(str(val), language=language.lower())
    elif isinstance(val, list):
        for v in val:
            if isinstance(v, dict):
                st.markdown("- " + " | ".join(f"**{k}:** {x}" for k, x in v.items()))
            else:
                st.markdown(f"- {v}")
    else:
        st.write(val)

if "data" in st.session_state:
    data = st.session_state.data
    res = data["result"]
    st.divider()
    if "quality_score" in res:
        st.metric("Code Quality Score", f"{res['quality_score']}/100")
    if data["static"]:
        with st.expander(f"Static analysis findings ({len(data['static'])})", expanded=True):
            for f in data["static"]:
                st.warning(f"Line {f['line']}: {f['message']}")
    for k, v in res.items():
        if k != "quality_score":
            render(k, v)
    m, l = st.session_state.meta
    st.download_button("Download Report (.md)", analyzer.to_markdown(m, l, data), "codepilot_report.md")
