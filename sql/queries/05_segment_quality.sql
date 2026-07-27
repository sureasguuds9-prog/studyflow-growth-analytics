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
