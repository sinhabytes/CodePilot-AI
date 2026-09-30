# CodePilot AI - Intelligent Code Review & Debugging Assistant
GenAI app that reviews code, finds bugs/security issues, fixes code, generates tests and explains code.

**Stack:** Python, Streamlit, Groq (llama-3.3-70b-versatile), Python `ast` static analysis, JSON-structured prompts.

## Run
```
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then put your Groq key inside
streamlit run app.py
```
## Deploy (Streamlit Cloud)
Push to GitHub → share.streamlit.io → select repo → app.py → Secrets: `GROQ_API_KEY = "..."`.

## Files
- `prompts.py` - 5 specialised prompts + JSON schemas
- `analyzer.py` - AST pre-checks, Groq call, JSON validation/retry, report builder
- `app.py` - Streamlit UI
