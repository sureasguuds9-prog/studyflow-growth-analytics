# -*- coding: utf-8 -*-
"""Run the StudyFlow product analytics pipeline and export portfolio artifacts."""
from pathlib import Path
import math
import sqlite3
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
PROCESSED = ROOT / 'data' / 'processed'
SQL_QUERIES = ROOT / 'sql' / 'queries'
SQL_ANSWERS = ROOT / 'sql' / 'answers'
REPORTS = ROOT / 'reports'
FIGURES = REPORTS / 'figures'
for p in [PROCESSED, SQL_QUERIES, SQL_ANSWERS, REPORTS, FIGURES]:
    p.mkdir(parents=True, exist_ok=True)


def df_to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    header = '| ' + ' | '.join(cols) + ' |'
    sep = '| ' + ' | '.join(['---'] * len(cols)) + ' |'
    rows = []
    for _, row in df.iterrows():
        values = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                values.append(f'{value:.4f}')
            else:
                values.append(str(value))
        rows.append('| ' + ' | '.join(values) + ' |')
    return '\n'.join([header, sep] + rows)

users = pd.read_csv(RAW / 'users.csv', parse_dates=['signup_date', 'assigned_at'])
events = pd.read_csv(RAW / 'events.csv', parse_dates=['event_time'])
payments = pd.read_csv(RAW / 'payments.csv', parse_dates=['payment_date'])
support = pd.read_csv(RAW / 'support_tickets.csv', parse_dates=['created_at'])
marketing = pd.read_csv(RAW / 'marketing_spend.csv', parse_dates=['date'])
ab = pd.read_csv(RAW / 'ab_assignments.csv', parse_dates=['assigned_at'])

active_users = users[users['is_test_account'] == False].copy()

# Core KPI definitions. Keep these aligned across Python and SQL.
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
kpi.to_frame('value').to_csv(PROCESSED / 'kpi_summary.csv')

funnel_steps = [
    ('signup', active_users['user_id'].nunique()),
    ('session_start', active_users.loc[active_users['sessions_7d'] > 0, 'user_id'].nunique()),
    ('lesson_started', active_users.loc[active_users['lessons_started_7d'] > 0, 'user_id'].nunique()),
    ('activated_7d', active_users.loc[active_users['activated_7d'], 'user_id'].nunique()),
    ('paywall_seen', active_users.loc[active_users['paywall_seen'], 'user_id'].nunique()),
    ('trial_started', active_users.loc[active_users['trial_started'], 'user_id'].nunique()),
    ('paid_14d', active_users.loc[active_users['paid_14d'], 'user_id'].nunique()),
    ('retained_30d', active_users.loc[active_users['retained_30d'], 'user_id'].nunique()),
]
funnel = pd.DataFrame(funnel_steps, columns=['step', 'users'])
funnel['from_signup_rate'] = funnel['users'] / funnel.loc[0, 'users']
funnel['step_to_step_rate'] = funnel['users'] / funnel['users'].shift(1)
funnel.to_csv(PROCESSED / 'funnel.csv', index=False)

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
channel.to_csv(PROCESSED / 'channel_unit_economics.csv', index=False)

cohort = active_users.groupby('cohort_month').agg(
    users=('user_id', 'nunique'),
    activation_rate=('activated_7d', 'mean'),
    paid_conversion=('paid_14d', 'mean'),
    retention_30d=('retained_30d', 'mean'),
    retention_60d=('retained_60d', 'mean'),
    arpu=('revenue_30d', 'mean'),
).reset_index()
cohort.to_csv(PROCESSED / 'cohort_metrics.csv', index=False)

segment = active_users.groupby('user_segment').agg(
    users=('user_id', 'nunique'),
    activation_rate=('activated_7d', 'mean'),
    paid_conversion=('paid_14d', 'mean'),
    arpu=('revenue_30d', 'mean'),
    retention_30d=('retained_30d', 'mean'),
    avg_lessons_completed=('lessons_completed_7d', 'mean'),
).sort_values('arpu', ascending=False).reset_index()
segment.to_csv(PROCESSED / 'segment_metrics.csv', index=False)

ab_summary = active_users.groupby('experiment_group').agg(
    users=('user_id', 'nunique'),
    activated=('activated_7d', 'sum'),
    payers=('paid_14d', 'sum'),
    arpu=('revenue_30d', 'mean'),
    retained_30d=('retained_30d', 'mean'),
    payment_failed_rate=('payment_failed', 'mean'),
    refund_rate=('refund_30d', 'mean'),
    avg_support_tickets=('support_tickets_30d', 'mean'),
    avg_nps=('nps_score', 'mean'),
)
ab_summary['activation_rate'] = ab_summary['activated'] / ab_summary['users']
ab_summary['paid_conversion'] = ab_summary['payers'] / ab_summary['users']

rows = []
for metric_name, success_col, rate_col in [
    ('activation_rate_7d', 'activated', 'activation_rate'),
    ('paid_conversion_14d', 'payers', 'paid_conversion'),
]:
    n1 = ab_summary.loc['control', 'users']
    n2 = ab_summary.loc['smart_onboarding', 'users']
    x1 = ab_summary.loc['control', success_col]
    x2 = ab_summary.loc['smart_onboarding', success_col]
    p1 = ab_summary.loc['control', rate_col]
    p2 = ab_summary.loc['smart_onboarding', rate_col]
    pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1/n1 + 1/n2))
    z = (p2 - p1) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    se_unpooled = math.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2)
    diff = p2 - p1
    rows.append({
        'metric': metric_name,
        'control': p1,
        'smart_onboarding': p2,
        'uplift_pp': diff * 100,
        'ci_low_pp': (diff - 1.96 * se_unpooled) * 100,
        'ci_high_pp': (diff + 1.96 * se_unpooled) * 100,
        'z_stat': z,
        'p_value': p_value,
        'significant_5pct': p_value < 0.05,
    })
ab_test = pd.DataFrame(rows)
ab_summary.reset_index().to_csv(PROCESSED / 'ab_summary.csv', index=False)
ab_test.to_csv(PROCESSED / 'ab_test_results.csv', index=False)

# Statistical checks beyond the experiment.
study_activated = active_users.loc[active_users['activated_7d'], 'study_minutes_7d']
study_not_activated = active_users.loc[~active_users['activated_7d'], 'study_minutes_7d']
t_stat, t_p = stats.ttest_ind(study_activated, study_not_activated, equal_var=False)
chi2, chi_p, _, _ = stats.chi2_contingency(pd.crosstab(active_users['device'], active_users['payment_failed']))
paid_cr = active_users['paid_14d'].mean()
paid_se = math.sqrt(paid_cr * (1 - paid_cr) / len(active_users))
arpu = active_users['revenue_30d'].mean()
arpu_se = active_users['revenue_30d'].std(ddof=1) / math.sqrt(len(active_users))
stats_summary = pd.DataFrame([
    {'test': 'paid_conversion_95_ci', 'statistic': paid_cr, 'p_value': np.nan, 'ci_low': paid_cr - 1.96*paid_se, 'ci_high': paid_cr + 1.96*paid_se},
    {'test': 'arpu_95_ci', 'statistic': arpu, 'p_value': np.nan, 'ci_low': arpu - 1.96*arpu_se, 'ci_high': arpu + 1.96*arpu_se},
    {'test': 'study_minutes_activated_vs_not_ttest', 'statistic': t_stat, 'p_value': t_p, 'ci_low': np.nan, 'ci_high': np.nan},
    {'test': 'device_vs_payment_failed_chi_square', 'statistic': chi2, 'p_value': chi_p, 'ci_low': np.nan, 'ci_high': np.nan},
    {'test': 'lessons_completed_vs_quiz_corr', 'statistic': active_users['lessons_completed_7d'].corr(active_users['quiz_score_after']), 'p_value': np.nan, 'ci_low': np.nan, 'ci_high': np.nan},
])
stats_summary.to_csv(PROCESSED / 'statistical_tests.csv', index=False)

# SQLite layer and SQL answers.
conn = sqlite3.connect(ROOT / 'data' / 'processed' / 'studyflow.sqlite')
for name, df in {
    'users': users,
    'events': events,
    'payments': payments,
    'support_tickets': support,
    'marketing_spend': marketing,
    'ab_assignments': ab,
}.items():
    df.to_sql(name, conn, index=False, if_exists='replace')

queries = {
    '01_funnel_by_variant.sql': """
WITH active_users AS (
    SELECT * FROM users WHERE is_test_account = 0
), funnel AS (
    SELECT experiment_group,
           COUNT(*) AS signups,
           SUM(CASE WHEN sessions_7d > 0 THEN 1 ELSE 0 END) AS started_session,
           SUM(CASE WHEN lessons_started_7d > 0 THEN 1 ELSE 0 END) AS started_lesson,
           SUM(CASE WHEN activated_7d THEN 1 ELSE 0 END) AS activated,
           SUM(CASE WHEN paywall_seen THEN 1 ELSE 0 END) AS paywall_seen,
           SUM(CASE WHEN trial_started THEN 1 ELSE 0 END) AS trial_started,
           SUM(CASE WHEN paid_14d THEN 1 ELSE 0 END) AS paid
    FROM active_users
    GROUP BY experiment_group
)
SELECT experiment_group, signups, started_session, started_lesson, activated, paywall_seen, trial_started, paid,
       1.0 * activated / signups AS activation_rate,
       1.0 * paid / signups AS paid_conversion
FROM funnel
ORDER BY experiment_group;
""",
    '02_channel_unit_economics.sql': """
WITH active_users AS (
    SELECT * FROM users WHERE is_test_account = 0
), channel_base AS (
    SELECT channel,
           COUNT(*) AS users,
           SUM(CASE WHEN paid_14d THEN 1 ELSE 0 END) AS payers,
           SUM(revenue_30d) AS revenue_30d,
           SUM(marketing_spend_user) AS spend,
           AVG(CASE WHEN retained_30d THEN 1.0 ELSE 0.0 END) AS retention_30d
    FROM active_users
    GROUP BY channel
)
SELECT channel, users, payers, revenue_30d, spend,
       1.0 * payers / users AS paid_conversion,
       1.0 * revenue_30d / users AS arpu,
       1.0 * spend / NULLIF(payers, 0) AS cac,
       1.0 * revenue_30d / NULLIF(spend, 0) AS roas,
       revenue_30d - spend AS profit_proxy,
       retention_30d
FROM channel_base
ORDER BY profit_proxy DESC;
""",
    '03_cohort_retention.sql': """
SELECT cohort_month,
       COUNT(*) AS users,
       AVG(CASE WHEN activated_7d THEN 1.0 ELSE 0.0 END) AS activation_rate,
       AVG(CASE WHEN paid_14d THEN 1.0 ELSE 0.0 END) AS paid_conversion,
       AVG(CASE WHEN retained_30d THEN 1.0 ELSE 0.0 END) AS retention_30d,
       AVG(CASE WHEN retained_60d THEN 1.0 ELSE 0.0 END) AS retention_60d,
       AVG(revenue_30d) AS arpu
FROM users
WHERE is_test_account = 0
GROUP BY cohort_month
ORDER BY cohort_month;
""",
    '04_top_device_channels.sql': """
WITH device_channel AS (
    SELECT device, channel,
           COUNT(*) AS users,
           AVG(CASE WHEN paid_14d THEN 1.0 ELSE 0.0 END) AS paid_conversion,
           AVG(revenue_30d) AS arpu
    FROM users
    WHERE is_test_account = 0
    GROUP BY device, channel
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY device ORDER BY paid_conversion DESC, arpu DESC) AS rn
    FROM device_channel
)
SELECT *
FROM ranked
WHERE rn <= 3
ORDER BY device, rn;
""",
    '05_segment_quality.sql': """
SELECT user_segment,
       COUNT(*) AS users,
       AVG(prior_sql_score) AS avg_prior_sql,
       AVG(lessons_completed_7d) AS avg_lessons_completed,
       AVG(CASE WHEN activated_7d THEN 1.0 ELSE 0.0 END) AS activation_rate,
       AVG(CASE WHEN paid_14d THEN 1.0 ELSE 0.0 END) AS paid_conversion,
       AVG(CASE WHEN retained_30d THEN 1.0 ELSE 0.0 END) AS retention_30d,
       AVG(revenue_30d) AS arpu
FROM users
WHERE is_test_account = 0
GROUP BY user_segment
ORDER BY arpu DESC;
""",
    '06_payment_failure_diagnostics.sql': """
SELECT device,
       COUNT(*) AS users,
       AVG(CASE WHEN payment_failed THEN 1.0 ELSE 0.0 END) AS payment_failed_rate,
       AVG(CASE WHEN paid_14d THEN 1.0 ELSE 0.0 END) AS paid_conversion,
       AVG(CASE WHEN refund_30d THEN 1.0 ELSE 0.0 END) AS refund_rate,
       AVG(support_tickets_30d) AS avg_support_tickets
FROM users
WHERE is_test_account = 0
GROUP BY device
ORDER BY payment_failed_rate DESC;
""",
    '07_support_topics.sql': """
SELECT topic,
       COUNT(*) AS tickets,
       AVG(resolution_hours) AS avg_resolution_hours,
       AVG(csat) AS avg_csat,
       SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) AS high_priority_tickets
FROM support_tickets
GROUP BY topic
ORDER BY tickets DESC;
""",
    '08_experiment_segments.sql': """
WITH segment_ab AS (
    SELECT user_segment, experiment_group,
           COUNT(*) AS users,
           AVG(CASE WHEN activated_7d THEN 1.0 ELSE 0.0 END) AS activation_rate,
           AVG(CASE WHEN paid_14d THEN 1.0 ELSE 0.0 END) AS paid_conversion,
           AVG(revenue_30d) AS arpu
    FROM users
    WHERE is_test_account = 0
    GROUP BY user_segment, experiment_group
), pivoted AS (
    SELECT user_segment,
           MAX(CASE WHEN experiment_group = 'control' THEN paid_conversion END) AS control_paid_conversion,
           MAX(CASE WHEN experiment_group = 'smart_onboarding' THEN paid_conversion END) AS smart_paid_conversion,
           MAX(CASE WHEN experiment_group = 'control' THEN activation_rate END) AS control_activation,
           MAX(CASE WHEN experiment_group = 'smart_onboarding' THEN activation_rate END) AS smart_activation
    FROM segment_ab
    GROUP BY user_segment
)
SELECT *,
       smart_paid_conversion - control_paid_conversion AS paid_conversion_diff,
       smart_activation - control_activation AS activation_diff
FROM pivoted
ORDER BY paid_conversion_diff DESC;
""",
    '09_revenue_share_by_channel.sql': """
WITH channel_revenue AS (
    SELECT channel, COUNT(*) AS users, SUM(revenue_30d) AS revenue, AVG(revenue_30d) AS arpu
    FROM users
    WHERE is_test_account = 0
    GROUP BY channel
)
SELECT channel, users, revenue, arpu,
       RANK() OVER (ORDER BY arpu DESC) AS arpu_rank,
       1.0 * revenue / SUM(revenue) OVER () AS revenue_share
FROM channel_revenue
ORDER BY arpu_rank;
""",
    '10_weekly_paid_conversion.sql': """
WITH weekly AS (
    SELECT strftime('%Y-%W', signup_date) AS signup_week,
           COUNT(*) AS users,
           SUM(CASE WHEN paid_14d THEN 1 ELSE 0 END) AS payers
    FROM users
    WHERE is_test_account = 0
    GROUP BY 1
)
SELECT signup_week, users, payers,
       1.0 * payers / users AS paid_conversion,
       AVG(1.0 * payers / users) OVER (ORDER BY signup_week ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS paid_conversion_4w_avg
FROM weekly
ORDER BY signup_week;
""",
}

sql_index_lines = ['# SQL-запросы и ответы\n\nВсе запросы выполняются против `data/processed/studyflow.sqlite`. Ответы сохранены в `sql/answers/`.\n\n']
for filename, sql in queries.items():
    qpath = SQL_QUERIES / filename
    qpath.write_text(sql.strip() + '\n', encoding='utf-8')
    answer = pd.read_sql_query(sql, conn)
    apath = SQL_ANSWERS / filename.replace('.sql', '.csv')
    answer.to_csv(apath, index=False)
    sql_index_lines.append(f'## {filename}\n\n```sql\n{sql.strip()}\n```\n\nОтвет: `sql/answers/{apath.name}`\n\n')
    sql_index_lines.append(df_to_markdown(answer.head(12)) + '\n\n')
(REPORTS / 'sql_queries_with_answers.md').write_text(''.join(sql_index_lines), encoding='utf-8')
conn.close()

# Charts
plt.style.use('default')
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(funnel['step'], funnel['users'], color='#2f6f9f')
ax.set_title('StudyFlow funnel')
ax.set_ylabel('Users')
ax.tick_params(axis='x', rotation=35)
fig.tight_layout()
fig.savefig(FIGURES / 'funnel.png', dpi=180)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
plot_channel = channel.sort_values('profit_proxy', ascending=True)
ax.barh(plot_channel['channel'], plot_channel['profit_proxy'], color='#3a7d44')
ax.set_title('Profit proxy by acquisition channel')
ax.set_xlabel('Revenue 30d - spend')
fig.tight_layout()
fig.savefig(FIGURES / 'channel_profit_proxy.png', dpi=180)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
cohort.plot(x='cohort_month', y=['paid_conversion', 'retention_30d'], marker='o', ax=ax)
ax.set_title('Cohort paid conversion and 30d retention')
ax.set_xlabel('Cohort month')
ax.set_ylabel('Rate')
fig.tight_layout()
fig.savefig(FIGURES / 'cohort_metrics.png', dpi=180)
plt.close(fig)

# JSON snapshot for docs.
snapshot = {
    'kpi': {k: float(v) for k, v in kpi.items()},
    'best_profit_channel': str(channel.iloc[0]['channel']),
    'best_paid_conversion_channel': str(channel.sort_values('paid_conversion', ascending=False).iloc[0]['channel']),
    'mobile_web_payment_failed_rate': float(active_users.loc[active_users['device'] == 'mobile_web', 'payment_failed'].mean()),
    'overall_payment_failed_rate': float(active_users['payment_failed'].mean()),
    'ab_results': ab_test.to_dict(orient='records'),
}
(REPORTS / 'analysis_snapshot.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')

print('Analysis complete')
print(kpi.round(4).to_string())
print('SQL answers:', len(list(SQL_ANSWERS.glob('*.csv'))))
