# analytics/db_connector.py
from urllib.parse import quote_plus
import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def get_db_config():
    """
    Returns DB config.
    Checks Streamlit secrets first (for cloud deployment),
    then falls back to local config.py.
    """
    try:
        if hasattr(st, 'secrets') and 'postgres' in st.secrets:
            return {
                'host':     st.secrets['postgres']['host'],
                'port':     int(st.secrets['postgres']['port']),
                'database': st.secrets['postgres']['database'],
                'user':     st.secrets['postgres']['user'],
                'password': st.secrets['postgres']['password'],
            }
    except Exception:
        pass
    from config_new import DB_CONFIG
    return DB_CONFIG

def get_engine():
    

    c = get_db_config()

    


    password = quote_plus(c["password"])

    url = (
        f"postgresql://{c['user']}:{password}"
        f"@{c['host']}:{c['port']}/{c['database']}"
    )

    

    return create_engine(url)

def query(sql: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)