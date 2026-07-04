# analytics/cohort_analysis.py
import pandas as pd
import numpy as np
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from analytics.db_connector import query

def load_data():
    return query("""
        SELECT fc.customer_id, fc.cohort_quarter,
               fc.first_purchase_date, fc.last_purchase_date,
               fc.total_orders, fc.total_revenue_usd,
               r.region_name
        FROM fact_customer fc
        JOIN dim_region r ON fc.region_key=r.region_key
    """)

def retention_matrix(df):
    df = df.copy()
    df['first'] = pd.to_datetime(df['first_purchase_date']).dt.to_period('Q')
    df['last']  = pd.to_datetime(df['last_purchase_date']).dt.to_period('Q')

    cohort_sizes = df.groupby('first')['customer_id'].nunique()
    results = {}

    for cohort, group in df.groupby('first'):
        size = len(group)
        row  = {}
        for offset in range(6):
            target   = cohort + offset
            retained = group[group['last'] >= target]['customer_id'].nunique()
            row[f'Q+{offset}'] = round(retained / size * 100, 1) if size > 0 else 0
        results[str(cohort)] = row

    retention_df = pd.DataFrame(results).T
    if 'Q+0' in retention_df.columns:
        retention_df['Q+0'] = 100.0

    os.makedirs('../data/processed', exist_ok=True)
    retention_df.to_csv('../data/processed/cohort_matrix.csv')
    return retention_df, cohort_sizes

def churn_signals(df):
    df = df.copy()
    df['last'] = pd.to_datetime(df['last_purchase_date'])
    latest = df['last'].max()
    df['inactive_days'] = (latest - df['last']).dt.days
    df['risk'] = pd.cut(
    df['inactive_days'],
    bins=[-1,120,270,540,9999],
    labels=['Active','Watch','At Risk','Churned']
   )
    s = df.groupby('risk', observed=True).agg(
        customers=('customer_id','count'),
        avg_rev  =('total_revenue_usd','mean'),
        total_rev=('total_revenue_usd','sum')
    ).round(2).reset_index()
    s['rev_pct'] = (s['total_rev']/s['total_rev'].sum()*100).round(2)
    return s

def run_cohort():
    df  = load_data()
    mat, sizes = retention_matrix(df)
    churn = churn_signals(df)
    q1  = mat.get('Q+1', pd.Series([0])).mean()
    q4  = mat.get('Q+4', pd.Series([0])).mean()
    return {'matrix': mat, 'sizes': sizes, 'churn': churn,
            'avg_q1_retention': round(q1,1),
            'avg_q4_retention': round(q4,1)}

if __name__ == '__main__':
    r = run_cohort()
    print(r['matrix'].head(5).to_string())
    print("\nChurn signals:")
    print(r['churn'].to_string(index=False))