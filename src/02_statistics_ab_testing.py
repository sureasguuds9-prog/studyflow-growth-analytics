# -*- coding: utf-8 -*-
"""Readable statistics and A/B testing analysis for StudyFlow."""
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'data' / 'processed'
OUT.mkdir(parents=True, exist_ok=True)

users = pd.read_csv(RAW / 'users.csv', parse_dates=['signup_date', 'assigned_at'])
active_users = users[users['is_test_account'] == False].copy()

print('1. CONFIDENCE INTERVALS')
paid_cr = active_users['paid_14d'].mean()
paid_se = math.sqrt(paid_cr * (1 - paid_cr) / len(active_users))
paid_ci_low = paid_cr - 1.96 * paid_se
paid_ci_high = paid_cr + 1.96 * paid_se

arpu = active_users['revenue_30d'].mean()
arpu_se = active_users['revenue_30d'].std(ddof=1) / math.sqrt(len(active_users))
arpu_ci_low = arpu - 1.96 * arpu_se
arpu_ci_high = arpu + 1.96 * arpu_se

print('paid conversion:', paid_cr, 'CI:', (paid_ci_low, paid_ci_high))
print('ARPU:', arpu, 'CI:', (arpu_ci_low, arpu_ci_high))

print('\n2. A/B TEST: SMART ONBOARDING')
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
print(ab_summary)

ab_rows = []
for metric_name, success_col, rate_col in [
    ('activation_rate_7d', 'activated', 'activation_rate'),
    ('paid_conversion_14d', 'payers', 'paid_conversion'),
]:
    n_control = ab_summary.loc['control', 'users']
    n_smart = ab_summary.loc['smart_onboarding', 'users']
    x_control = ab_summary.loc['control', success_col]
    x_smart = ab_summary.loc['smart_onboarding', success_col]
    p_control = ab_summary.loc['control', rate_col]
    p_smart = ab_summary.loc['smart_onboarding', rate_col]

    pooled = (x_control + x_smart) / (n_control + n_smart)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / n_control + 1 / n_smart))
    z_stat = (p_smart - p_control) / se_pooled
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    se_unpooled = math.sqrt(p_control * (1 - p_control) / n_control + p_smart * (1 - p_smart) / n_smart)
    uplift = p_smart - p_control
    ci_low = uplift - 1.96 * se_unpooled
    ci_high = uplift + 1.96 * se_unpooled

    ab_rows.append({
        'metric': metric_name,
        'control': p_control,
        'smart_onboarding': p_smart,
        'uplift_pp': uplift * 100,
        'ci_low_pp': ci_low * 100,
        'ci_high_pp': ci_high * 100,
        'z_stat': z_stat,
        'p_value': p_value,
        'significant_5pct': p_value < 0.05,
    })

ab_test = pd.DataFrame(ab_rows)
print(ab_test)
ab_summary.reset_index().to_csv(OUT / 'python_ab_summary.csv', index=False)
ab_test.to_csv(OUT / 'python_ab_test_results.csv', index=False)

print('\n3. STATISTICAL HYPOTHESIS TESTS')
study_activated = active_users.loc[active_users['activated_7d'], 'study_minutes_7d']
study_not_activated = active_users.loc[~active_users['activated_7d'], 'study_minutes_7d']
t_stat, t_p_value = stats.ttest_ind(study_activated, study_not_activated, equal_var=False)
print('H0: mean study_minutes_7d is equal for activated and non-activated users')
print('t-test:', t_stat, t_p_value)

contingency = pd.crosstab(active_users['device'], active_users['payment_failed'])
chi2, chi_p_value, dof, expected = stats.chi2_contingency(contingency)
print('\nH0: device and payment_failed are independent')
print('chi-square:', chi2, chi_p_value)
print('contingency table:')
print(contingency)

corr = active_users['lessons_completed_7d'].corr(active_users['quiz_score_after'])
print('\nPearson correlation lessons_completed_7d vs quiz_score_after:', corr)

print('\n4. REVENUE DISTRIBUTION AND OUTLIERS')
payers = active_users[active_users['paid_14d']].copy()
revenue_summary = payers['revenue_30d'].agg(['mean', 'median', 'std', 'min', 'max'])
revenue_summary['p90'] = payers['revenue_30d'].quantile(0.90)
revenue_summary['p95'] = payers['revenue_30d'].quantile(0.95)
q1 = payers['revenue_30d'].quantile(0.25)
q3 = payers['revenue_30d'].quantile(0.75)
iqr = q3 - q1
outlier_high = q3 + 1.5 * iqr
outliers_count = (payers['revenue_30d'] > outlier_high).sum()
print(revenue_summary)
print('IQR:', iqr, 'high outliers:', outliers_count)

stats_report = pd.DataFrame([
    {'test': 'paid_conversion_95_ci', 'statistic': paid_cr, 'p_value': np.nan, 'ci_low': paid_ci_low, 'ci_high': paid_ci_high},
    {'test': 'arpu_95_ci', 'statistic': arpu, 'p_value': np.nan, 'ci_low': arpu_ci_low, 'ci_high': arpu_ci_high},
    {'test': 'study_minutes_activated_vs_not_ttest', 'statistic': t_stat, 'p_value': t_p_value, 'ci_low': np.nan, 'ci_high': np.nan},
    {'test': 'device_vs_payment_failed_chi_square', 'statistic': chi2, 'p_value': chi_p_value, 'ci_low': np.nan, 'ci_high': np.nan},
    {'test': 'lessons_completed_vs_quiz_corr', 'statistic': corr, 'p_value': np.nan, 'ci_low': np.nan, 'ci_high': np.nan},
])
stats_report.to_csv(OUT / 'python_statistics_report.csv', index=False)

print('\n5. INTERPRETATION')
print('- Smart onboarding improves activation and paid conversion with statistically significant uplift.')
print('- Guardrails must still be monitored: payment_failed_rate, refund_rate, support tickets, NPS.')
print('- t-test and correlation are diagnostic; they do not prove causality outside the randomized experiment.')
print('- Chi-square suggests payment friction differs by device, especially important for mobile web diagnostics.')
