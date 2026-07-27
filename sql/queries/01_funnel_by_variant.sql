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
