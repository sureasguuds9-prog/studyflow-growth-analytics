# -*- coding: utf-8 -*-
"""Readable Python/Pandas product analytics for StudyFlow.

This file is intentionally analysis-first: it shows the exact code used to
clean data, calculate product metrics, build funnels, cohorts, channel unit
economics, and segment findings.
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'data' / 'processed'
OUT.mkdir(parents=True, exist_ok=True)

users = pd.read_csv(RAW / 'users.csv', parse_dates=['signup_date', 'assigned_at'])
events = pd.read_csv(RAW / 'events.csv', parse_dates=['event_time'])
payments = pd.read_csv(RAW / 'payments.csv', parse_dates=['payment_date'])
support = pd.read_csv(RAW / 'support_tickets.csv', parse_dates=['created_at'])
marketing = pd.read_csv(RAW / 'marketing_spend.csv', parse_dates=['date'])

print('1. DATA QUALITY')
print('users shape:', users.shape)
print('events shape:', events.shape)
print('payments shape:', payments.shape)
print('support shape:', support.shape)
print('marketing shape:', marketing.shape)
print('user_id unique:', users['user_id'].is_unique)

missing = users.isna().sum().sort_values(ascending=False)
missing = missing[missing > 0]
missing_report = pd.DataFrame({'missing_rows': missing, 'missing_share': missing / len(users)})
print('\nMissing values in users:')
print(missing_report)

active_users = users[users['is_test_account'] == False].copy()
print('\nExcluded test accounts:', len(users) - len(active_users))

print('\n2. CORE PRODUCT KPI')
kpi = pd.Series({
    'users': active_users['user_id'].nunique(),
    'activation_rate_7d': active_users['activated_7d'].mean(),
    'trial_start_rate_7d': active_users['trial_started'].mean(),
    'paid_conversion_14d': active_users['paid_14d'].mean(),
    'arpu_30d': active_users['revenue_30d'].mean(),
    'arppu_30d': active_users.loc[active_users['paid_14d'], 'revenue_30d'].mean(),
    'retention_30d': active_users['retained_30d'].mean(),
    'retention_60d': active_users['retained_60d'].mean(),
    'refund_rate_payers_30d': active_users.loc[active_users['paid_14d'], 'refund_30d'].mean(),
    'payment_failed_rate': active_users['payment_failed'].mean(),
    'avg_nps': active_users['nps_score'].mean(),
})
print(kpi)
kpi.to_frame('value').to_csv(OUT / 'python_kpi_summary.csv')

print('\n3. FUNNEL')
funnel = pd.DataFrame([
    {'step': 'signup', 'users': active_users['user_id'].nunique()},
    {'step': 'session_start', 'users': active_users.loc[active_users['sessions_7d'] > 0, 'user_id'].nunique()},
    {'step': 'lesson_started', 'users': active_users.loc[active_users['lessons_started_7d'] > 0, 'user_id'].nunique()},
    {'step': 'activated_7d', 'users': active_users.loc[active_users['activated_7d'], 'user_id'].nunique()},
    {'step': 'paywall_seen', 'users': active_users.loc[active_users['paywall_seen'], 'user_id'].nunique()},
    {'step': 'trial_started', 'users': active_users.loc[active_users['trial_started'], 'user_id'].nunique()},
    {'step': 'paid_14d', 'users': active_users.loc[active_users['paid_14d'], 'user_id'].nunique()},
    {'step': 'retained_30d', 'users': active_users.loc[active_users['retained_30d'], 'user_id'].nunique()},
])
funnel['from_signup_rate'] = funnel['users'] / funnel.loc[0, 'users']
funnel['step_to_step_rate'] = funnel['users'] / funnel['users'].shift(1)
print(funnel)
funnel.to_csv(OUT / 'python_funnel.csv', index=False)

print('\n4. CHANNEL UNIT ECONOMICS')
channel = active_users.groupby('channel').agg(
    users=('user_id', 'nunique'),
    activated=('activated_7d', 'sum'),
    payers=('paid_14d', 'sum'),
    revenue_30d=('revenue_30d', 'sum'),
    spend=('marketing_spend_user', 'sum'),
    retained_30d=('retained_30d', 'sum'),
    refunds=('refund_30d', 'sum'),
    payment_failed=('payment_failed', 'sum'),
).reset_index()
channel['activation_rate'] = channel['activated'] / channel['users']
channel['paid_conversion'] = channel['payers'] / channel['users']
channel['arpu'] = channel['revenue_30d'] / channel['users']
channel['cac'] = channel['spend'] / channel['payers'].replace(0, np.nan)
channel['roas'] = channel['revenue_30d'] / channel['spend'].replace(0, np.nan)
channel['profit_proxy'] = channel['revenue_30d'] - channel['spend']
channel['retention_30d'] = channel['retained_30d'] / channel['users']
channel['refund_rate'] = channel['refunds'] / channel['payers'].replace(0, np.nan)
channel['payment_failed_rate'] = channel['payment_failed'] / channel['users']
channel = channel.sort_values('profit_proxy', ascending=False)
print(channel)
channel.to_csv(OUT / 'python_channel_unit_economics.csv', index=False)

print('\n5. COHORTS')
cohort = active_users.groupby('cohort_month').agg(
    users=('user_id', 'nunique'),
    activation_rate=('activated_7d', 'mean'),
    paid_conversion=('paid_14d', 'mean'),
    retention_30d=('retained_30d', 'mean'),
    retention_60d=('retained_60d', 'mean'),
    arpu=('revenue_30d', 'mean'),
).reset_index()
print(cohort)
cohort.to_csv(OUT / 'python_cohort_metrics.csv', index=False)

print('\n6. SEGMENTS')
segment = active_users.groupby('user_segment').agg(
    users=('user_id', 'nunique'),
    activation_rate=('activated_7d', 'mean'),
    paid_conversion=('paid_14d', 'mean'),
    arpu=('revenue_30d', 'mean'),
    retention_30d=('retained_30d', 'mean'),
    avg_lessons_completed=('lessons_completed_7d', 'mean'),
).sort_values('arpu', ascending=False).reset_index()
print(segment)
segment.to_csv(OUT / 'python_segment_metrics.csv', index=False)

print('\n7. BUSINESS FINDINGS')
print('- Activation is high, but paid conversion is the main bottleneck after paywall/trial.')
print('- Organic, email, and referral are economically stronger than paid channels by profit proxy.')
print('- Mobile web should be checked for payment friction because payment failure is elevated.')
print('- Segment strategy should prioritize high-ARPU and high-retention groups, not only volume.')
