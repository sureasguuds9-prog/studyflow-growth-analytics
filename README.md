# StudyFlow Growth Analytics: Activation, Conversion & Retention

Полноценный портфолио-проект по продуктовой аналитике SaaS/EdTech-продукта. Проект отвечает на бизнес-вопрос:

> Как StudyFlow увеличить оплату и удержание пользователей, не ухудшая refund, payment failures, support load и NPS?

Данные синтетические, но воспроизводимые и спроектированы как реалистичный продуктовый кейс: пользователи, события, платежи, support, маркетинговые расходы и A/B-тест smart onboarding.

## Executive Summary

- В выборке `5141` активных пользователей после исключения тестовых аккаунтов.
- Activation 7d: `69.4%`; paid conversion 14d: `22.3%`.
- ARPU 30d: `387`; ARPPU 30d: `1 733`.
- Smart onboarding дал uplift activation на `16.89 п.п.` и paid conversion на `7.37 п.п.`; оба результата статистически значимы на 5%.
- Лучший канал по profit proxy: `organic`; лучший канал по paid conversion: `email`.
- Самый высокий payment failure rate по устройствам: `mobile_web` (`7.0%`).

## Что показывает проект

- Python/Pandas: чистка данных, витрины, продуктовые KPI, cohorts, unit economics, A/B и статистика.
- SQL: 10 готовых аналитических запросов с сохранёнными ответами.
- Статистика: z-test для долей, доверительные интервалы, t-test, chi-square, correlation.
- BI-мышление: dashboard spec, метрики, guardrails, рекомендации.
- Business storytelling: цель, выводы, ограничения, action plan.

## Структура

```text
studyflow-growth-analytics/
├── data/
│   ├── raw/                 # исходные CSV-таблицы
│   └── processed/           # витрины, KPI, SQLite
├── docs/
│   ├── data_dictionary.md
│   ├── dashboard_spec.md
│   ├── methodology.md
│   └── interview_defense.md
├── notebooks/
│   ├── 01_studyflow_product_analysis.ipynb
│   └── 02_full_python_statistics_sql_ab_analysis.ipynb
├── reports/
│   ├── analytical_report.md
│   ├── sql_queries_with_answers.md
│   └── figures/
├── sql/
│   ├── queries/             # SQL-запросы
│   └── answers/             # результаты запросов
└── src/
    ├── generate_data.py
    └── run_analysis.py
```

## Как воспроизвести

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/generate_data.py
python src/run_analysis.py
```

## Где код анализа

- `src/01_python_product_analytics.py` — Python/Pandas анализ продукта: KPI, funnel, каналы, когорты, сегменты.
- `src/02_statistics_ab_testing.py` — статистика и A/B: CI, z-test, t-test, chi-square, correlation.
- `src/03_run_sql_queries.py` — запуск SQL-запросов и сохранение ответов.
- `notebooks/02_full_python_statistics_sql_ab_analysis.ipynb` — полный notebook с Python, статистикой, A/B и SQL.
- `reports/ANALYTICS_CODE_AND_FINDINGS.md` — кодовые блоки рядом с выводами.

## Главные артефакты

- [Итоговый аналитический отчёт](reports/analytical_report.md)
- [SQL-запросы с ответами](reports/sql_queries_with_answers.md)
- [Словарь данных](docs/data_dictionary.md)
- [Dashboard specification](docs/dashboard_spec.md)
- [Защита проекта на собеседовании](docs/interview_defense.md)

## Решение для бизнеса

1. Rollout smart onboarding можно рекомендовать: он улучшает activation и paid conversion, при этом guardrails нужно продолжать мониторить.
2. Маркетинговый бюджет нельзя перераспределять только по paid conversion: нужен profit proxy, CAC, ROAS и retention.
3. Mobile web требует отдельного расследования payment friction, потому что payment failures выше среднего.
4. Growth-команде нужно оптимизировать связку `activation -> trial -> paid -> retained`, а не одну изолированную метрику.

## Ограничения

- Данные синтетические, поэтому выводы демонстрируют методологию, а не реальное состояние компании.
- Revenue рассчитан в 30-дневном окне, LTV является приближением.
- A/B-тест сгенерирован как рандомизированный эксперимент; в реальной компании нужна проверка SRM, логирования и пересечений экспериментов.
