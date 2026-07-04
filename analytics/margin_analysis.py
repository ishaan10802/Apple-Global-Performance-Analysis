# analytics/margin_analysis.py
import pandas as pd
import numpy as np
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from analytics.db_connector import query

def load_margin():
    return query("SELECT * FROM vw_product_margin ORDER BY fiscal_year,fiscal_quarter")

def load_exec():
    return query("SELECT * FROM vw_executive_summary ORDER BY fiscal_year,fiscal_quarter")

def product_pl(df: pd.DataFrame) -> pd.DataFrame:
    """True TTM = last 4 complete quarters only."""
    quarters = (
        df[['fiscal_year', 'fiscal_quarter']]
        .drop_duplicates()
        .sort_values(['fiscal_year', 'fiscal_quarter'])
    )
    last_4 = quarters.tail(4).copy()
    last_4['_k'] = (last_4['fiscal_year'].astype(str)
                    + '_' + last_4['fiscal_quarter'].astype(str))

    df = df.copy()
    df['_k'] = (df['fiscal_year'].astype(str)
                + '_' + df['fiscal_quarter'].astype(str))
    ttm = df[df['_k'].isin(last_4['_k'])]

    pl = ttm.groupby('product_name').agg(
        ttm_rev_m  =('revenue_usd_millions',  'sum'),
        ttm_gp_m   =('gross_profit_usd_millions', 'sum'),
        avg_margin =('gross_margin_pct',       'mean'),
        ttm_units  =('units_millions',         'sum'),
    ).round(2).reset_index()

    pl['rev_mix_pct'] = (pl['ttm_rev_m'] / pl['ttm_rev_m'].sum() * 100).round(2)
    pl['gp_mix_pct']  = (pl['ttm_gp_m']  / pl['ttm_gp_m'].sum()  * 100).round(2)

    os.makedirs('../data/processed', exist_ok=True)
    pl.to_csv('../data/processed/margin_summary.csv', index=False)
    return pl.sort_values('ttm_rev_m', ascending=False)

def margin_trend(df):
    return df.groupby(
        ['fiscal_year','fiscal_quarter','quarter_label','product_category']
    ).agg(
        revenue     =('revenue_usd_millions','sum'),
        gross_profit=('gross_profit_usd_millions','sum')
    ).reset_index().assign(
        margin_pct=lambda x:(x['gross_profit']/x['revenue']*100).round(2)
    )

def services_premium(df):
    by_cat = df.groupby(
        ['fiscal_year','fiscal_quarter','quarter_label','product_category']
    ).agg(rev=('revenue_usd_millions','sum'),
          gp =('gross_profit_usd_millions','sum')).reset_index()
    by_cat['m'] = (by_cat['gp']/by_cat['rev']*100).round(2)
    piv = by_cat.pivot_table(
        index=['fiscal_year','fiscal_quarter','quarter_label'],
        columns='product_category', values='m'
    ).reset_index()
    if 'Services' in piv.columns and 'Hardware' in piv.columns:
        piv['premium_pp'] = (piv['Services']-piv['Hardware']).round(2)
    return piv

def run_margin():
    df   = load_margin()
    exec_df = load_exec()
    pl   = product_pl(df)
    trend = margin_trend(df)
    prem = services_premium(df)
    latest = exec_df.iloc[-1]
    return {
        'pl_table':       pl,
        'margin_trend':   trend,
        'svc_premium':    prem,
        'latest_margin':  latest['blended_gross_margin_pct'],
        'latest_svc_mix': latest['services_mix_pct'],
        'latest_ttm':     latest['ttm_revenue_millions'],
    }

if __name__ == '__main__':
    r = run_margin()
    print(r['pl_table'].to_string(index=False))