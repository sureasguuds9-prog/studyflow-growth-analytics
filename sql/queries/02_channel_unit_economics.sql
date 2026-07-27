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
