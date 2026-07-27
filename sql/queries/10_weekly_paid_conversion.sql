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
