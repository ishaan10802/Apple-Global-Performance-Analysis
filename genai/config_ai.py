# genai/config_ai.py
"""
OpenAI API configuration.
Reads key from Streamlit secrets (cloud) or config.py (local).
Import get_openai_client() everywhere you need the API.
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def get_openai_client():
    """
    Return an authenticated OpenAI client.
    Priority order:
      1. Streamlit secrets (when running on Streamlit Cloud)
      2. config.py OPENAI_API_KEY variable (local dev)
      3. OPENAI_API_KEY environment variable
    """
    from openai import OpenAI
    key = None

    # 1. Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
          key = (
        st.secrets.get("OPENAI_API_KEY")
        or st.secrets.get("openai_api_key")
    )
    except Exception:
        pass

    # 2. config.py
    if not key:
        try:
            from config_new import OPENAI_API_KEY
            key = OPENAI_API_KEY
        except ImportError:
            pass

    # 3. Environment variable
    if not key:
        key = os.environ.get("OPENAI_API_KEY", "")

    if not key or "your" in key.lower() or len(key) < 20:
        raise ValueError(
            "OpenAI API key not configured.\n"
            "Add it to config.py: OPENAI_API_KEY = 'sk-...'\n"
            "Or to .streamlit/secrets.toml: openai_api_key = 'sk-...'"
        )

    return OpenAI(api_key=key)


MODEL      = "gpt-4o"
MAX_TOKENS = 1000
TEMP_FACTS = 0.2    # low temperature for factual SQL/analysis responses
TEMP_PROSE = 0.4    # slightly higher for narrative writing