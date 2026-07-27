# SQL-запросы и ответы

Все запросы выполняются против `data/processed/studyflow.sqlite`. Ответы сохранены в `sql/answers/`.

## 01_funnel_by_variant.sql

```sql
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
```

Ответ: `sql/answers/01_funnel_by_variant.csv`

| experiment_group | signups | started_session | started_lesson | activated | paywall_seen | trial_started | paid | activation_rate | paid_conversion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| control | 2567 | 2532 | 2488 | 1565 | 2463 | 617 | 479 | 0.6097 | 0.1866 |
| smart_onboarding | 2574 | 2558 | 2530 | 2004 | 2532 | 799 | 670 | 0.7786 | 0.2603 |

## 02_channel_unit_economics.sql

```sql
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
```

Ответ: `sql/answers/02_channel_unit_economics.csv`

| channel | users | payers | revenue_30d | spend | paid_conversion | arpu | cac | roas | profit_proxy | retention_30d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| organic | 1574 | 334 | 558440.0000 | 0.0000 | 0.2122 | 354.7903 | 0.0000 | nan | 558440.0000 | 0.4104 |
| email | 594 | 164 | 299060.0000 | 44573.8700 | 0.2761 | 503.4680 | 271.7919 | 6.7093 | 254486.1300 | 0.4545 |
| referral | 595 | 136 | 256880.0000 | 77301.5400 | 0.2286 | 431.7311 | 568.3937 | 3.3231 | 179578.4600 | 0.4807 |
| influencer | 348 | 87 | 150510.0000 | 215533.6500 | 0.2500 | 432.5000 | 2477.3983 | 0.6983 | -65023.6500 | 0.4253 |
| paid_social | 900 | 191 | 317920.0000 | 387367.7200 | 0.2122 | 353.2444 | 2028.1032 | 0.8207 | -69447.7200 | 0.4089 |
| paid_search | 1130 | 237 | 408880.0000 | 580611.6800 | 0.2097 | 361.8407 | 2449.8383 | 0.7042 | -171731.6800 | 0.4372 |

## 03_cohort_retention.sql

```sql
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
```

Ответ: `sql/answers/03_cohort_retention.csv`

| cohort_month | users | activation_rate | paid_conversion | retention_30d | retention_60d | arpu |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01 | 873 | 0.6873 | 0.2211 | 0.4112 | 0.2153 | 394.4559 |
| 2026-02 | 802 | 0.7020 | 0.2257 | 0.4214 | 0.2032 | 381.6209 |
| 2026-03 | 844 | 0.6801 | 0.2393 | 0.4419 | 0.2204 | 440.3791 |
| 2026-04 | 871 | 0.6877 | 0.2009 | 0.4110 | 0.2124 | 335.8324 |
| 2026-05 | 903 | 0.7010 | 0.2259 | 0.4551 | 0.2182 | 374.5515 |
| 2026-06 | 848 | 0.7075 | 0.2288 | 0.4399 | 0.2229 | 399.5991 |

## 04_top_device_channels.sql

```sql
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
```

Ответ: `sql/answers/04_top_device_channels.csv`

| device | channel | users | paid_conversion | arpu | rn |
| --- | --- | --- | --- | --- | --- |
| android | email | 200 | 0.2600 | 477.1000 | 1 |
| android | influencer | 124 | 0.2258 | 400.4839 | 2 |
| android | paid_search | 365 | 0.2192 | 385.2329 | 3 |
| desktop | influencer | 66 | 0.3030 | 557.1212 | 1 |
| desktop | referral | 103 | 0.3010 | 482.0388 | 2 |
| desktop | email | 138 | 0.2899 | 511.2319 | 3 |
| ios | email | 174 | 0.3161 | 579.3103 | 1 |
| ios | referral | 189 | 0.2487 | 386.2963 | 2 |
| ios | influencer | 126 | 0.2460 | 406.1111 | 3 |
| mobile_web | influencer | 32 | 0.2500 | 403.4375 | 1 |
| mobile_web | referral | 94 | 0.2340 | 788.5106 | 2 |
| mobile_web | organic | 232 | 0.2155 | 364.0948 | 3 |

## 05_segment_quality.sql

```sql
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
```

Ответ: `sql/answers/05_segment_quality.csv`

| user_segment | users | avg_prior_sql | avg_lessons_completed | activation_rate | paid_conversion | retention_30d | arpu |
| --- | --- | --- | --- | --- | --- | --- | --- |
| junior_analyst | 1062 | 54.2149 | 4.2693 | 0.8277 | 0.3098 | 0.4859 | 544.9058 |
| career_switcher | 1631 | 39.2207 | 3.1349 | 0.6806 | 0.2140 | 0.4341 | 375.6223 |
| other | 495 | 38.4895 | 2.9455 | 0.6141 | 0.2141 | 0.3737 | 368.2626 |
| manager | 769 | 43.3917 | 2.9493 | 0.6229 | 0.1860 | 0.3810 | 333.4590 |
| student | 1184 | 39.7173 | 3.1816 | 0.6731 | 0.1875 | 0.4307 | 305.4392 |

## 06_payment_failure_diagnostics.sql

```sql
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
```

Ответ: `sql/answers/06_payment_failure_diagnostics.csv`

| device | users | payment_failed_rate | paid_conversion | refund_rate | avg_support_tickets |
| --- | --- | --- | --- | --- | --- |
| mobile_web | 704 | 0.0696 | 0.2145 | 0.0185 | 0.1960 |
| ios | 1589 | 0.0554 | 0.2240 | 0.0138 | 0.1416 |
| desktop | 1132 | 0.0495 | 0.2420 | 0.0124 | 0.1069 |
| android | 1716 | 0.0460 | 0.2145 | 0.0117 | 0.1002 |

## 07_support_topics.sql

```sql
SELECT topic,
       COUNT(*) AS tickets,
       AVG(resolution_hours) AS avg_resolution_hours,
       AVG(csat) AS avg_csat,
       SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) AS high_priority_tickets
FROM support_tickets
GROUP BY topic
ORDER BY tickets DESC;
```

Ответ: `sql/answers/07_support_topics.csv`

| topic | tickets | avg_resolution_hours | avg_csat | high_priority_tickets |
| --- | --- | --- | --- | --- |
| payment | 178 | 17.2365 | 4.0506 | 28 |
| course_content | 159 | 15.6007 | 4.0314 | 19 |
| technical_issue | 144 | 16.6408 | 3.9931 | 19 |
| refund | 95 | 21.6116 | 4.1158 | 12 |
| account | 86 | 18.1193 | 3.9767 | 12 |

## 08_experiment_segments.sql

```sql
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
```

Ответ: `sql/answers/08_experiment_segments.csv`

| user_segment | control_paid_conversion | smart_paid_conversion | control_activation | smart_activation | paid_conversion_diff | activation_diff |
| --- | --- | --- | --- | --- | --- | --- |
| other | 0.1619 | 0.2661 | 0.5506 | 0.6774 | 0.1042 | 0.1268 |
| career_switcher | 0.1658 | 0.2606 | 0.5873 | 0.7708 | 0.0947 | 0.1835 |
| student | 0.1443 | 0.2303 | 0.5806 | 0.7647 | 0.0859 | 0.1841 |
| junior_analyst | 0.2889 | 0.3308 | 0.7636 | 0.8922 | 0.0419 | 0.1286 |
| manager | 0.1692 | 0.2038 | 0.5278 | 0.7239 | 0.0346 | 0.1961 |

## 09_revenue_share_by_channel.sql

```sql
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
```

Ответ: `sql/answers/09_revenue_share_by_channel.csv`

| channel | users | revenue | arpu | arpu_rank | revenue_share |
| --- | --- | --- | --- | --- | --- |
| email | 594 | 299060.0000 | 503.4680 | 1 | 0.1502 |
| influencer | 348 | 150510.0000 | 432.5000 | 2 | 0.0756 |
| referral | 595 | 256880.0000 | 431.7311 | 3 | 0.1290 |
| paid_search | 1130 | 408880.0000 | 361.8407 | 4 | 0.2053 |
| organic | 1574 | 558440.0000 | 354.7903 | 5 | 0.2804 |
| paid_social | 900 | 317920.0000 | 353.2444 | 6 | 0.1596 |

## 10_weekly_paid_conversion.sql

```sql
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
```

Ответ: `sql/answers/10_weekly_paid_conversion.csv`

| signup_week | users | payers | paid_conversion | paid_conversion_4w_avg |
| --- | --- | --- | --- | --- |
| 2026-00 | 103 | 24 | 0.2330 | 0.2330 |
| 2026-01 | 200 | 59 | 0.2950 | 0.2640 |
| 2026-02 | 204 | 40 | 0.1961 | 0.2414 |
| 2026-03 | 194 | 31 | 0.1598 | 0.2210 |
| 2026-04 | 201 | 47 | 0.2338 | 0.2212 |
| 2026-05 | 195 | 49 | 0.2513 | 0.2102 |
| 2026-06 | 197 | 37 | 0.1878 | 0.2082 |
| 2026-07 | 209 | 51 | 0.2440 | 0.2292 |
| 2026-08 | 205 | 45 | 0.2195 | 0.2257 |
| 2026-09 | 191 | 44 | 0.2304 | 0.2204 |
| 2026-10 | 194 | 49 | 0.2526 | 0.2366 |
| 2026-11 | 190 | 48 | 0.2526 | 0.2388 |

