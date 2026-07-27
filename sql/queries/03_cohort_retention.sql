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
