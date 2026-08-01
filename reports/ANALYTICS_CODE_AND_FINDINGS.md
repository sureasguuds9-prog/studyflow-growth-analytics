# Python, статистика, A/B-тест и SQL: код с выводами

Этот файл отвечает на вопрос “где код?”. В проекте теперь есть отдельные readable-скрипты, notebook и отчёт с кодом.

## Где лежит код

- `src/01_python_product_analytics.py` — Python/Pandas: качество данных, KPI, funnel, channel economics, cohorts, segments.
- `src/02_statistics_ab_testing.py` — статистика: CI, t-test, chi-square, correlation, A/B z-test.
- `src/03_run_sql_queries.py` — запуск всех SQL-запросов и сохранение ответов.
- `notebooks/02_full_python_statistics_sql_ab_analysis.ipynb` — полный notebook по блокам.
- `sql/queries/` — отдельные SQL-запросы.
- `sql/answers/` — готовые ответы SQL.

## 1. Python/Pandas: загрузка и качество данных

```python
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'

users = pd.read_csv(RAW / 'users.csv', parse_dates=['signup_date', 'assigned_at'])
events = pd.read_csv(RAW / 'events.csv', parse_dates=['event_time'])
payments = pd.read_csv(RAW / 'payments.csv', parse_dates=['payment_date'])
support = pd.read_csv(RAW / 'support_tickets.csv', parse_dates=['created_at'])
marketing = pd.read_csv(RAW / 'marketing_spend.csv', parse_dates=['date'])

active_users = users[users['is_test_account'] == False].copy()
missing = users.isna().sum().sort_values(ascending=False)
missing = missing[missing > 0]
missing_report = pd.DataFrame({'missing_rows': missing, 'missing_share': missing / len(users)})
```

**Вывод:** `user_id` уникален, тестовые аккаунты исключены, основные пропуски находятся в `csat`, `age`, `region`. `csat` пропущен у пользователей без support ticket, поэтому это не ошибка, а особенность события.

## 2. Продуктовая аналитика: KPI

```python
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
```

| Метрика | Значение |
|---|---:|
| Users | 5141 |
| Activation 7d | 69.4% |
| Trial start 7d | 27.5% |
| Paid conversion 14d | 22.3% |
| ARPU 30d | 387 |
| ARPPU 30d | 1 733 |
| Retention 30d | 43.0% |
| Retention 60d | 21.6% |

**Вывод:** activation уже высокая, но paid conversion заметно ниже activation. Главная продуктовая зона роста: связка `activation -> trial -> paid`.

## 3. Охват продуктовых этапов

```python
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
```

| step | users | from_signup_rate | step_to_step_rate |
| --- | --- | --- | --- |
| signup | 5141 | 1.0000 | nan |
| session_start | 5090 | 0.9901 | 0.9901 |
| lesson_started | 5018 | 0.9761 | 0.9859 |
| activated_7d | 3569 | 0.6942 | 0.7112 |
| paywall_seen | 4995 | 0.9716 | 1.3996 |
| trial_started | 1416 | 0.2754 | 0.2835 |
| paid_14d | 1149 | 0.2235 | 0.8114 |
| retained_30d | 2212 | 0.4303 | 1.9252 |

**Вывод:** воронка показывает, что пользователь в основном доходит до обучения и paywall, но монетизация требует отдельной оптимизации.

## 4. Юнит-экономика каналов

```python
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
channel['paid_conversion'] = channel['payers'] / channel['users']
channel['arpu'] = channel['revenue_30d'] / channel['users']
channel['cac'] = channel['spend'] / channel['payers'].replace(0, np.nan)
channel['roas'] = channel['revenue_30d'] / channel['spend'].replace(0, np.nan)
channel['profit_proxy'] = channel['revenue_30d'] - channel['spend']
```

| channel | users | payers | paid_conversion | arpu | cac | roas | profit_proxy | retention_30d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| organic | 1574 | 334 | 0.2122 | 354.7903 | 0.0000 | nan | 558440.0000 | 0.4104 |
| email | 594 | 164 | 0.2761 | 503.4680 | 271.7919 | 6.7093 | 254486.1300 | 0.4545 |
| referral | 595 | 136 | 0.2286 | 431.7311 | 568.3937 | 3.3231 | 179578.4600 | 0.4807 |
| influencer | 348 | 87 | 0.2500 | 432.5000 | 2477.3983 | 0.6983 | -65023.6500 | 0.4253 |
| paid_social | 900 | 191 | 0.2122 | 353.2444 | 2028.1032 | 0.8207 | -69447.7200 | 0.4089 |
| paid_search | 1130 | 237 | 0.2097 | 361.8407 | 2449.8383 | 0.7042 | -171731.6800 | 0.4372 |

**Вывод:** лучший канал по profit proxy: `organic`. Лучший канал по paid conversion: `email`. Это разные управленческие вопросы, поэтому нельзя выбирать канал только по одной метрике.

## 5. Статистика: доверительный интервал, t-тест, хи-квадрат и корреляция

```python
paid_cr = active_users['paid_14d'].mean()
paid_se = math.sqrt(paid_cr * (1 - paid_cr) / len(active_users))
paid_ci_low = paid_cr - 1.96 * paid_se
paid_ci_high = paid_cr + 1.96 * paid_se

arpu = active_users['revenue_30d'].mean()
arpu_se = active_users['revenue_30d'].std(ddof=1) / math.sqrt(len(active_users))
arpu_ci_low = arpu - 1.96 * arpu_se
arpu_ci_high = arpu + 1.96 * arpu_se

t_stat, t_p_value = stats.ttest_ind(
    active_users.loc[active_users['activated_7d'], 'study_minutes_7d'],
    active_users.loc[~active_users['activated_7d'], 'study_minutes_7d'],
    equal_var=False
)

contingency = pd.crosstab(active_users['device'], active_users['payment_failed'])
chi2, chi_p_value, dof, expected = stats.chi2_contingency(contingency)

corr = active_users['lessons_completed_7d'].corr(active_users['quiz_score_after'])
```

| test | statistic | p_value | ci_low | ci_high |
| --- | --- | --- | --- | --- |
| paid_conversion_95_ci | 0.2235 | nan | 0.2121 | 0.2349 |
| arpu_95_ci | 387.4130 | nan | 362.0279 | 412.7980 |
| study_minutes_activated_vs_not_ttest | 61.5499 | 0.0000 | nan | nan |
| device_vs_payment_failed_chi_square | 5.9931 | 0.1119 | nan | nan |
| lessons_completed_vs_quiz_corr | 0.6725 | nan | nan | nan |

**Вывод:** статистика здесь разделена на causal и diagnostic. A/B можно трактовать причинно при корректной рандомизации. t-test, chi-square и correlation дают диагностические сигналы, но не доказывают причинность.

## 6. A/B-тест умного онбординга

```python
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
```

```python
# z-test для двух долей
pooled = (x_control + x_smart) / (n_control + n_smart)
se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / n_control + 1 / n_smart))
z_stat = (p_smart - p_control) / se_pooled
p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
```

| metric | control | smart_onboarding | uplift_pp | ci_low_pp | ci_high_pp | z_stat | p_value | significant_5pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activation_rate_7d | 0.6097 | 0.7786 | 16.8894 | 14.4126 | 19.3662 | 13.1418 | 0.0000 | True |
| paid_conversion_14d | 0.1866 | 0.2603 | 7.3696 | 5.1013 | 9.6379 | 6.3421 | 0.0000 | True |

**Вывод:** smart onboarding повышает activation на `16.89 п.п.` и paid conversion на `7.37 п.п.`. Оба эффекта статистически значимы. Рекомендация: rollout с monitoring guardrails.

## 7. SQL: запросы и ответы

SQL лежит отдельно:

- `sql/queries/01_funnel_by_variant.sql`
- `sql/queries/02_channel_unit_economics.sql`
- `sql/queries/03_cohort_retention.sql`
- `sql/queries/04_top_device_channels.sql`
- `sql/queries/05_segment_quality.sql`
- `sql/queries/06_payment_failure_diagnostics.sql`
- `sql/queries/07_support_topics.sql`
- `sql/queries/08_experiment_segments.sql`
- `sql/queries/09_revenue_share_by_channel.sql`
- `sql/queries/10_weekly_paid_conversion.sql`

Пример SQL:

```sql
WITH channel_base AS (
    SELECT channel,
           COUNT(*) AS users,
           SUM(CASE WHEN paid_14d THEN 1 ELSE 0 END) AS payers,
           SUM(revenue_30d) AS revenue_30d,
           SUM(marketing_spend_user) AS spend
    FROM users
    WHERE is_test_account = 0
    GROUP BY channel
)
SELECT channel, users, payers, revenue_30d, spend,
       1.0 * payers / users AS paid_conversion,
       1.0 * spend / NULLIF(payers, 0) AS cac,
       1.0 * revenue_30d / NULLIF(spend, 0) AS roas,
       revenue_30d - spend AS profit_proxy
FROM channel_base
ORDER BY profit_proxy DESC;
```

Полный файл с SQL и ответами: `reports/sql_queries_with_answers.md`.

## 8. Финальные выводы

1. Smart onboarding — validated growth lever: повышает activation и paid conversion.
2. Главный bottleneck — не старт обучения, а переход от learning value к оплате.
3. Каналы нужно оценивать через `profit_proxy`, `CAC`, `ROAS`, retention, а не только conversion.
4. Payment friction нужно расследовать отдельно по устройствам и платежному flow.
5. Для управления продуктом нужен dashboard: funnel, acquisition economics, cohorts, A/B, support/payment guardrails.
