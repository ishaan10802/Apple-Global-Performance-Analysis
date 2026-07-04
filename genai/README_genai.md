# GenAI Layer — Apple Global Performance Analysis Platform

This module adds a GPT-4o powered intelligence layer on top
of the PostgreSQL warehouse and Python analytics engine.

---

## Setup

### 1. Install dependencies
```bash
pip install openai==1.30.0
```

### 2. Add your API key

**Local development** — open `config.py` and set:
```python
OPENAI_API_KEY = "sk-your-key-here"
```

**Streamlit Cloud** — add to Secrets dashboard:
```toml
openai_api_key = "sk-your-key-here"
```

---

## Four GenAI Modules

### `insight_engine.py`
Pulls live KPIs from PostgreSQL and writes a professional
executive quarterly commentary using GPT-4o.

```bash
python genai/insight_engine.py
```
Output: `exports/ai_narratives/executive_insight_[timestamp].txt`

---

### `narrative_writer.py`
Generates a complete five-section executive report:
1. Financial Summary
2. Services Business Analysis
3. Customer Intelligence
4. Geographic Risk Assessment
5. Strategic Outlook

```bash
python genai/narrative_writer.py
```
Output: `exports/ai_narratives/full_narrative_[timestamp].txt`

---

### `anomaly_explainer.py`
Detects statistically unusual revenue movements using
z-scores and asks GPT-4o to explain each in business context.

```bash
python genai/anomaly_explainer.py
```
Output: `exports/ai_narratives/anomaly_report_[timestamp].txt`

---

### Natural Language Q&A (in `insight_engine.py`)
Ask any business question in plain English via `answer_question()`.
Used by the Streamlit AI Insights page.

Example questions:
- "Which product had the highest gross margin this year?"
- "How has China's revenue share changed since FY2022?"
- "What is the Services attach rate trend over 4 quarters?"

---

## API Cost Estimate

| Module | GPT-4o calls | Cost per run |
|---|---|---|
| Insight Engine | 1 | ~$0.02 |
| Narrative Writer | 5 | ~$0.08 |
| Anomaly Explainer | up to 12 | ~$0.12 |
| Q&A (per question) | 1 | ~$0.01 |

**Full demo run: under $0.25 USD**

---
