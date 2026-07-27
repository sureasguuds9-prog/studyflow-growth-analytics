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
