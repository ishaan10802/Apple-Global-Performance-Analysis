import pandas as pd
import streamlit as st

from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

from config_new import DB_CONFIG


def get_db_config():
    """
    Priority:
    1. Streamlit secrets
    2. config_new.py (.env / Render environment variables)
    """

    try:
        if "postgres" in st.secrets:
            return {
                "host": st.secrets["postgres"]["host"],
                "port": st.secrets["postgres"]["port"],
                "database": st.secrets["postgres"]["database"],
                "user": st.secrets["postgres"]["user"],
                "password": st.secrets["postgres"]["password"],
            }
    except Exception:
        pass

    return DB_CONFIG


def get_engine():

    c = get_db_config()

    password = quote_plus(str(c["password"]))

    url = (
        f"postgresql+psycopg2://"
        f"{c['user']}:{password}"
        f"@{c['host']}:{c['port']}"
        f"/{c['database']}"
    )

    return create_engine(url)


def query(sql, params=None):

    engine = get_engine()

    with engine.connect() as conn:
        return pd.read_sql(
            text(sql),
            conn,
            params=params,
        )