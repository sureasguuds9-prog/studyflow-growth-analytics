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
