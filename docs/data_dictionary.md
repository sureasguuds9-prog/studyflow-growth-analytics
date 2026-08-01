# Словарь данных

## users.csv

- `user_id` — уникальный ID пользователя.
- `signup_date` — дата регистрации.
- `cohort_month` — месяц регистрации.
- `channel` — канал привлечения.
- `device` — основное устройство.
- `region` — регион.
- `user_segment` — учебно-профессиональный сегмент.
- `age` — возраст, есть пропуски.
- `prior_python_score`, `prior_sql_score` — стартовая оценка навыков.
- `experiment_group` — группа A/B-теста.
- `sessions_7d`, `lessons_started_7d`, `lessons_completed_7d`, `study_minutes_7d` — активность за первые 7 дней.
- `activated_7d` — пользователь выполнил условие активации.
- `paywall_seen`, `trial_started`, `paid_14d` — события монетизации.
- `monthly_price`, `revenue_30d` — цена и выручка.
- `refund_30d`, `payment_failed` — защитные платёжные метрики.
- `retained_30d`, `retained_60d`, `churned_60d` — удержание и отток.
- `support_tickets_30d`, `csat`, `nps_score` — поддержка и пользовательский опыт.
- `marketing_spend_user` — атрибутированные расходы на привлечение.
- `is_test_account` — тестовый аккаунт.

## events.csv

Событийная таблица: `signup`, `session_start`, `lesson_started`, `lesson_completed`, `paywall_seen`, `trial_started`, `subscription_paid`, `return_30d`.

## payments.csv

Платежи и неуспешные попытки оплаты: `paid`, `refunded`, `failed`.

## support_tickets.csv

Обращения в поддержку: тема, приоритет, время решения и CSAT.

## marketing_spend.csv

Дневные расходы по каналам.

## ab_assignments.csv

Назначение в эксперимент `smart_onboarding_v1`.
