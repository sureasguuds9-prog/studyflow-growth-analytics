# Methodology

## Тип анализа

- Descriptive: базовые KPI, funnel, cohorts, channel economics.
- Diagnostic: payment failures, support topics, segment quality.
- Experiment evaluation: A/B smart onboarding.
- Prescriptive: рекомендации по rollout, marketing allocation и payment diagnostics.

## Ключевые определения

- `activation_rate_7d`: доля пользователей, завершивших 3+ урока за 7 дней или показавших достаточную активность.
- `paid_conversion_14d`: доля пользователей, оплативших в первые 14 дней.
- `ARPU 30d`: средняя выручка на всех активных пользователей за 30 дней.
- `ARPPU 30d`: средняя выручка на платящих пользователей.
- `profit_proxy`: `revenue_30d - marketing_spend_user`.
- `retention_30d`: доля пользователей, вернувшихся через 30 дней.

## Почему эти методы

- Funnel показывает, где теряется пользователь.
- Cohort analysis отделяет качество новых регистраций по месяцам.
- Unit economics не даёт переоценить каналы с дорогим трафиком.
- A/B test нужен для causal inference по onboarding.
- Guardrails защищают от краткосрочного роста ценой ухудшения опыта.

## Статистическая осторожность

- `p-value` не является вероятностью истинности гипотезы.
- Корреляция learning activity и retention не доказывает причинность.
- Для реального rollout нужна проверка SRM, логирования и независимости эксперимента.
