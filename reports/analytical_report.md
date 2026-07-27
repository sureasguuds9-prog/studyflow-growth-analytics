# Analytical Report: StudyFlow Growth Analytics

## 1. Цель анализа

StudyFlow — обучающий SaaS/EdTech-продукт для начинающих аналитиков. Бизнес-команда хочет понять, как увеличить платящую конверсию и удержание без роста негативных guardrails: refund, payment failures, support tickets и падения NPS.

Главный вопрос:

> Какой ростовый рычаг стоит масштабировать: onboarding, маркетинговые каналы, сегментные CRM-цепочки или исправление payment friction?

## 2. Данные и качество

Использованы таблицы:

- `users.csv` — пользовательская витрина и продуктовые флаги.
- `events.csv` — событийная таблица funnel-логики.
- `payments.csv` — оплаты и failed/refunded платежи.
- `support_tickets.csv` — обращения и CSAT.
- `marketing_spend.csv` — дневные расходы по каналам.
- `ab_assignments.csv` — назначение пользователей в эксперимент.

Исключены `is_test_account = True`. Основные риски качества: пропуски в `age`, `region`, `csat`, revenue outliers и leakage-поля после оплаты.

## 3. KPI Summary

| Метрика | Значение |
|---|---:|
| Users | 5141 |
| Activation 7d | 69.4% |
| Trial start 7d | 27.5% |
| Paid conversion 14d | 22.3% |
| ARPU 30d | 387 |
| ARPPU 30d | 1 733 |
| Retention 30d | 43.0% |
| Retention 60d | 21.6% |
| Refund rate among payers | 6.0% |
| Payment failed rate | 5.3% |
| Avg NPS | 6.95 |

## 4. Funnel

Главная воронка:

| Step | Users | From signup |
|---|---:|---:|
| signup | 5141 | 100.0% |
| session_start | 5090 | 99.0% |
| lesson_started | 5018 | 97.6% |
| activated_7d | 3569 | 69.4% |
| paywall_seen | 4995 | 97.2% |
| trial_started | 1416 | 27.5% |
| paid_14d | 1149 | 22.3% |
| retained_30d | 2212 | 43.0% |


Ключевой провал воронки находится между activation/trial и оплатой: активация высокая, но до оплаты доходит `22.3%` пользователей. Поэтому ростовая стратегия должна работать не только с привлечением, но и с моментом paywall и perceived learning value.

## 5. Channel Unit Economics

Топ каналов по profit proxy:

| Channel | Users | Paid conversion | ARPU | CAC | ROAS | Profit proxy | Retention 30d |
|---|---:|---:|---:|---:|---:|---:|---:|
| organic | 1574 | 21.2% | 355 | 0 | nan | 558 440 | 41.0% |
| email | 594 | 27.6% | 503 | 272 | 6.71 | 254 486 | 45.5% |
| referral | 595 | 22.9% | 432 | 568 | 3.32 | 179 578 | 48.1% |
| influencer | 348 | 25.0% | 432 | 2 477 | 0.70 | -65 024 | 42.5% |
| paid_social | 900 | 21.2% | 353 | 2 028 | 0.82 | -69 448 | 40.9% |
| paid_search | 1130 | 21.0% | 362 | 2 450 | 0.70 | -171 732 | 43.7% |


Вывод: `organic`, `email` и `referral` выглядят сильнее по экономике, чем paid channels. Paid channels дают объём, но требуют оптимизации CAC и качества трафика.

## 6. A/B-тест smart onboarding

| Metric | Control | Smart onboarding | Uplift, п.п. | p-value | Decision |
|---|---:|---:|---:|---:|---|
| activation_rate_7d | 61.0% | 77.9% | 16.89 | 0.000000 | significant |
| paid_conversion_14d | 18.7% | 26.0% | 7.37 | 0.000000 | significant |


Интерпретация: smart onboarding статистически значимо повышает и activation, и paid conversion. Это даёт основание для rollout, но только вместе с guardrail monitoring.

## 7. Statistical Checks

- 95% CI для paid conversion: см. `data/processed/statistical_tests.csv`.
- t-test показывает существенную разницу study minutes между activated и non-activated пользователями. Это диагностическая связь, а не causal proof.
- Chi-square показывает связь между устройством и payment failed. На практике это сигнал для технической диагностики mobile web/payment flow.
- Корреляция lessons completed и quiz score положительная, что соответствует продуктовой логике learning value.

## 8. Основные выводы

1. **Smart onboarding — главный validated growth lever.** Он повышает activation и paid conversion с хорошей статистической поддержкой.
2. **Маркетинг нужно оптимизировать по экономике, а не по объёму регистраций.** Paid channels требуют CAC/ROAS контроля.
3. **Mobile web payment friction — отдельный технический риск.** Устройство с максимальным payment failed rate: `mobile_web`.
4. **Retention связан с активацией.** Growth должен смотреть на activation quality, а не только на paid conversion.
5. **Support/refund/NPS должны быть guardrails.** Иначе можно купить краткосрочную оплату ценой будущего churn.

## 9. Рекомендации

- Rollout `smart_onboarding_v1` на 100% пользователей, но с недельным мониторингом `payment_failed_rate`, `refund_rate`, `support_tickets_30d`, `NPS`.
- Перераспределить бюджет из слабых paid channels в email/referral mechanics и в оптимизацию paid_search targeting.
- Запустить отдельный payment diagnostics project для `mobile_web`: логи ошибок, шаг оплаты, браузеры, методы оплаты.
- Добавить CRM-цепочку для activated non-payers: пользователь уже получил learning value, но не оплатил.
- Построить постоянный dashboard с воронкой, каналами, retention cohorts и guardrails.

## 10. Ограничения

Данные синтетические и используются для демонстрации аналитического мышления и владения инструментами. В реальном бизнесе нужны дополнительные проверки: SRM, event logging QA, causal design, LTV over longer horizon, incremental lift по маркетинговым каналам.
