# -*- coding: utf-8 -*-
"""Generate a reproducible synthetic SaaS/EdTech product dataset for StudyFlow."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
RAW.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(20260627)

n_users = 5200
start = pd.Timestamp('2026-01-01')
end = pd.Timestamp('2026-06-30')
channels = np.array(['organic', 'paid_search', 'paid_social', 'email', 'referral', 'influencer'])
devices = np.array(['ios', 'android', 'desktop', 'mobile_web'])
segments = np.array(['career_switcher', 'student', 'junior_analyst', 'manager', 'other'])
regions = np.array(['Moscow', 'Saint Petersburg', 'Kazan', 'Yekaterinburg', 'Novosibirsk', 'Other'])

signup_date = start + pd.to_timedelta(rng.integers(0, (end - start).days + 1, n_users), unit='D')
channel = rng.choice(channels, n_users, p=[0.30, 0.22, 0.17, 0.12, 0.12, 0.07])
device = rng.choice(devices, n_users, p=[0.31, 0.33, 0.22, 0.14])
segment = rng.choice(segments, n_users, p=[0.31, 0.23, 0.21, 0.15, 0.10])
region = rng.choice(regions, n_users, p=[0.35, 0.17, 0.10, 0.09, 0.08, 0.21]).astype(object)
age = np.clip(rng.normal(28.2, 6.4, n_users).round(), 18, 55).astype(float)
prior_python = np.clip(rng.normal(43, 18, n_users) + (segment == 'junior_analyst')*13 + (segment == 'student')*5, 0, 100).round(1)
prior_sql = np.clip(rng.normal(39, 17, n_users) + (segment == 'junior_analyst')*15 + (segment == 'manager')*4, 0, 100).round(1)
experiment_group = rng.choice(['control', 'smart_onboarding'], n_users, p=[0.50, 0.50])
assigned_at = signup_date + pd.to_timedelta(rng.integers(0, 2, n_users), unit='D')

base_engagement = (
    1.45
    + (channel == 'email') * 0.52
    + (channel == 'referral') * 0.46
    + (device == 'desktop') * 0.33
    + (segment == 'junior_analyst') * 0.58
    + (segment == 'career_switcher') * 0.25
    + (experiment_group == 'smart_onboarding') * 0.31
)
sessions_7d = np.clip(rng.poisson(np.clip(base_engagement * 2.5, 0.5, 8.5)), 0, 20)
lessons_started_7d = np.clip(rng.poisson(0.9 + sessions_7d * 0.9 + (experiment_group == 'smart_onboarding') * 0.40), 0, 32)
completion_p = np.clip(0.26 + prior_python/270 + prior_sql/330 + (experiment_group == 'smart_onboarding')*0.052 - (device == 'mobile_web')*0.06, 0.04, 0.93)
lessons_completed_7d = np.array([rng.binomial(int(s), float(p)) if s > 0 else 0 for s, p in zip(lessons_started_7d, completion_p)])
study_minutes_7d = np.clip(rng.gamma(2.25, 22, n_users) + lessons_completed_7d*18 + sessions_7d*7, 0, 1000).round(1)
activated_7d = (lessons_completed_7d >= 3) | ((sessions_7d >= 4) & (lessons_completed_7d >= 2))
paywall_seen = (sessions_7d >= 2) | (lessons_started_7d >= 2)
trial_prob = np.clip(0.09 + activated_7d*0.23 + (channel == 'email')*0.04 + (channel == 'referral')*0.04 + (experiment_group == 'smart_onboarding')*0.03 - (device == 'mobile_web')*0.03, 0.02, 0.70)
trial_started = rng.random(n_users) < trial_prob
paid_prob = np.clip(0.035 + trial_started*0.36 + activated_7d*0.09 + (prior_sql > 60)*0.035 + (segment == 'junior_analyst')*0.04 + (experiment_group == 'smart_onboarding')*0.020, 0.01, 0.78)
paid_14d = rng.random(n_users) < paid_prob
price = rng.choice([990, 1490, 1990, 2990], n_users, p=[0.34, 0.35, 0.22, 0.09])
monthly_price = np.where(paid_14d, price, 0)
revenue_30d = np.where(paid_14d, price * rng.choice([1, 1, 1, 2], n_users, p=[0.71, 0.14, 0.10, 0.05]), 0).astype(float)
paid_idx = np.where(paid_14d)[0]
if len(paid_idx):
    outliers = rng.choice(paid_idx, size=min(18, len(paid_idx)), replace=False)
    revenue_30d[outliers] *= rng.choice([3, 4, 5], len(outliers), p=[0.55, 0.30, 0.15])
refund_30d = paid_14d & (rng.random(n_users) < np.clip(0.065 + (device == 'mobile_web')*0.040 + (lessons_completed_7d <= 1)*0.045, 0.01, 0.24))
payment_failed = paywall_seen & (rng.random(n_users) < np.clip(0.045 + (device == 'mobile_web')*0.030 + (channel == 'paid_social')*0.015, 0.005, 0.22))
retained_30d = rng.random(n_users) < np.clip(0.12 + activated_7d*0.36 + paid_14d*0.23 + (experiment_group == 'smart_onboarding')*0.025, 0.02, 0.90)
retained_60d = retained_30d & (rng.random(n_users) < np.clip(0.34 + paid_14d*0.28 + lessons_completed_7d/50, 0.05, 0.84))
churned_60d = paid_14d & ~retained_60d
support_tickets_30d = rng.poisson(0.08 + payment_failed*0.55 + refund_30d*0.68 + (device == 'mobile_web')*0.06, n_users)
csat = np.where(support_tickets_30d > 0, np.clip(rng.normal(4.18 - refund_30d*0.60 - payment_failed*0.35, 0.75, n_users).round(), 1, 5), np.nan)
nps_score = np.clip(rng.normal(6.1 + activated_7d*1.15 + paid_14d*0.75 - refund_30d*1.55 - payment_failed*0.85, 1.8, n_users).round(), 0, 10)
quiz_score_after = np.clip(prior_python*0.35 + prior_sql*0.25 + lessons_completed_7d*4.6 + rng.normal(18, 11, n_users), 0, 100).round(1)

marketing_spend_user = np.select(
    [channel == 'paid_search', channel == 'paid_social', channel == 'influencer', channel == 'email', channel == 'referral', channel == 'organic'],
    [rng.normal(520,110,n_users), rng.normal(430,130,n_users), rng.normal(610,180,n_users), rng.normal(75,18,n_users), rng.normal(130,35,n_users), np.zeros(n_users)],
    default=0
)
marketing_spend_user = np.clip(marketing_spend_user, 0, None).round(2)

is_test_account = rng.random(n_users) < 0.012
age[rng.choice(np.arange(n_users), 130, replace=False)] = np.nan
region[rng.choice(np.arange(n_users), 105, replace=False)] = np.nan

users = pd.DataFrame({
    'user_id': [f'U{i:06d}' for i in range(1, n_users + 1)],
    'signup_date': signup_date,
    'cohort_month': pd.Series(signup_date).dt.to_period('M').astype(str).to_numpy(),
    'channel': channel,
    'device': device,
    'region': region,
    'user_segment': segment,
    'age': age,
    'prior_python_score': prior_python,
    'prior_sql_score': prior_sql,
    'experiment_group': experiment_group,
    'assigned_at': assigned_at,
    'sessions_7d': sessions_7d,
    'lessons_started_7d': lessons_started_7d,
    'lessons_completed_7d': lessons_completed_7d,
    'study_minutes_7d': study_minutes_7d,
    'activated_7d': activated_7d,
    'paywall_seen': paywall_seen,
    'trial_started': trial_started,
    'paid_14d': paid_14d,
    'monthly_price': monthly_price,
    'revenue_30d': revenue_30d.round(2),
    'refund_30d': refund_30d,
    'payment_failed': payment_failed,
    'retained_30d': retained_30d,
    'retained_60d': retained_60d,
    'churned_60d': churned_60d,
    'support_tickets_30d': support_tickets_30d,
    'csat': csat,
    'nps_score': nps_score,
    'quiz_score_after': quiz_score_after,
    'marketing_spend_user': marketing_spend_user,
    'is_test_account': is_test_account,
})

ab_assignments = users[['user_id', 'experiment_group', 'assigned_at']].copy()
ab_assignments['experiment_name'] = 'smart_onboarding_v1'

payments = users.loc[users['paid_14d'], ['user_id', 'signup_date', 'monthly_price', 'revenue_30d', 'refund_30d', 'payment_failed']].copy()
payments['payment_id'] = [f'PAY{i:06d}' for i in range(1, len(payments) + 1)]
payments['payment_date'] = payments['signup_date'] + pd.to_timedelta(rng.integers(0, 15, len(payments)), unit='D')
payments['payment_status'] = np.where(payments['refund_30d'], 'refunded', 'paid')
payments['amount'] = payments['revenue_30d']
payments = payments[['payment_id', 'user_id', 'payment_date', 'payment_status', 'amount', 'monthly_price']]

failed = users.loc[users['payment_failed'], ['user_id', 'signup_date']].copy()
failed['payment_id'] = [f'FAIL{i:06d}' for i in range(1, len(failed) + 1)]
failed['payment_date'] = failed['signup_date'] + pd.to_timedelta(rng.integers(0, 15, len(failed)), unit='D')
failed['payment_status'] = 'failed'
failed['amount'] = 0.0
failed['monthly_price'] = 0
payments = pd.concat([payments, failed[['payment_id', 'user_id', 'payment_date', 'payment_status', 'amount', 'monthly_price']]], ignore_index=True)

support_rows = []
for _, row in users[users['support_tickets_30d'] > 0].iterrows():
    for j in range(int(row['support_tickets_30d'])):
        topic = rng.choice(['payment', 'course_content', 'technical_issue', 'refund', 'account'], p=[0.28, 0.22, 0.25, 0.13, 0.12])
        priority = rng.choice(['low', 'medium', 'high'], p=[0.45, 0.42, 0.13])
        created = row['signup_date'] + pd.to_timedelta(int(rng.integers(0, 31)), unit='D') + pd.to_timedelta(int(rng.integers(8*60, 23*60)), unit='m')
        resolution_hours = max(1, rng.gamma(2.1, 7.5) + (priority == 'high')*5 + (topic == 'refund')*4)
        support_rows.append({
            'ticket_id': f'T{len(support_rows) + 1:06d}',
            'user_id': row['user_id'],
            'created_at': created,
            'topic': topic,
            'priority': priority,
            'resolution_hours': round(float(resolution_hours), 2),
            'csat': row['csat'] if not pd.isna(row['csat']) else np.nan,
        })
support_tickets = pd.DataFrame(support_rows)

spend_rows = []
for date in pd.date_range(start, end, freq='D'):
    for ch in ['paid_search', 'paid_social', 'email', 'referral', 'influencer']:
        base = {'paid_search': 15000, 'paid_social': 12500, 'email': 1800, 'referral': 3400, 'influencer': 6200}[ch]
        spend_rows.append({
            'date': date,
            'channel': ch,
            'spend': round(float(max(0, rng.normal(base, base*0.18))), 2),
        })
marketing_spend = pd.DataFrame(spend_rows)

# Event-level table for funnel checks.
event_rows = []
for _, row in users.iterrows():
    uid = row['user_id']
    base_date = row['signup_date']
    event_rows.append({'user_id': uid, 'event_time': base_date, 'event_name': 'signup', 'session_id': f'{uid}_S000'})
    if row['sessions_7d'] > 0:
        for s in range(int(row['sessions_7d'])):
            session_id = f'{uid}_S{s+1:03d}'
            session_time = base_date + pd.to_timedelta(int(rng.integers(0, 8*24*60)), unit='m')
            event_rows.append({'user_id': uid, 'event_time': session_time, 'event_name': 'session_start', 'session_id': session_id})
    for k in range(int(row['lessons_started_7d'])):
        event_rows.append({'user_id': uid, 'event_time': base_date + pd.to_timedelta(int(rng.integers(0, 8*24*60)), unit='m'), 'event_name': 'lesson_started', 'session_id': f'{uid}_L{k+1:03d}'})
    for k in range(int(row['lessons_completed_7d'])):
        event_rows.append({'user_id': uid, 'event_time': base_date + pd.to_timedelta(int(rng.integers(0, 8*24*60)), unit='m'), 'event_name': 'lesson_completed', 'session_id': f'{uid}_C{k+1:03d}'})
    if row['paywall_seen']:
        event_rows.append({'user_id': uid, 'event_time': base_date + pd.to_timedelta(int(rng.integers(0, 8*24*60)), unit='m'), 'event_name': 'paywall_seen', 'session_id': f'{uid}_P001'})
    if row['trial_started']:
        event_rows.append({'user_id': uid, 'event_time': base_date + pd.to_timedelta(int(rng.integers(0, 8*24*60)), unit='m'), 'event_name': 'trial_started', 'session_id': f'{uid}_TR001'})
    if row['paid_14d']:
        event_rows.append({'user_id': uid, 'event_time': base_date + pd.to_timedelta(int(rng.integers(0, 15*24*60)), unit='m'), 'event_name': 'subscription_paid', 'session_id': f'{uid}_PAY001'})
    if row['retained_30d']:
        event_rows.append({'user_id': uid, 'event_time': base_date + pd.to_timedelta(int(rng.integers(30*24*60, 35*24*60)), unit='m'), 'event_name': 'return_30d', 'session_id': f'{uid}_R30'})

events = pd.DataFrame(event_rows)

users.to_csv(RAW / 'users.csv', index=False)
ab_assignments.to_csv(RAW / 'ab_assignments.csv', index=False)
payments.to_csv(RAW / 'payments.csv', index=False)
support_tickets.to_csv(RAW / 'support_tickets.csv', index=False)
marketing_spend.to_csv(RAW / 'marketing_spend.csv', index=False)
events.to_csv(RAW / 'events.csv', index=False)

print('Generated raw tables:')
for file in sorted(RAW.glob('*.csv')):
    print(file.name, pd.read_csv(file).shape)
