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
