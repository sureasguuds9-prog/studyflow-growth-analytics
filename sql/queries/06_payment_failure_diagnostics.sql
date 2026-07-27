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
