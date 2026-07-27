# Interview Defense Notes

## 60-second pitch

Я сделал end-to-end продуктовый аналитический проект для StudyFlow, SaaS/EdTech-продукта для обучения аналитиков. Главный вопрос: как увеличить оплату и удержание пользователей, не ухудшая refund, payment failures, support load и NPS. Я сгенерировал воспроизводимые продуктовые данные, построил Python/Pandas pipeline, SQLite-слой, 10 SQL-запросов с ответами, funnel, cohort analysis, channel unit economics и A/B-тест smart onboarding. Главный вывод: smart onboarding можно выкатывать, потому что он статистически значимо повышает activation и paid conversion, но rollout должен идти с guardrail monitoring. Дополнительно я нашёл, что маркетинг нужно оценивать по profit proxy/CAC/ROAS, а mobile web требует payment diagnostics.

## 10 вопросов и ответы

1. **Почему проект не просто EDA?**  
Потому что есть бизнес-вопрос, KPI framework, SQL layer, A/B, guardrails и рекомендации.

2. **Какая главная метрика?**  
Связка `activation_rate_7d -> paid_conversion_14d -> retention_30d`, а не одна isolated metric.

3. **Почему нельзя смотреть только paid conversion?**  
Потому что можно ухудшить refunds, support load, NPS или привлечь дорогой трафик с плохой экономикой.

4. **Как ты оценивал A/B?**  
Для activation и paid conversion использовал z-test для двух долей, uplift в п.п. и guardrails.

5. **Что показал A/B?**  
Activation uplift `16.89 п.п.`, paid conversion uplift `7.37 п.п.`, оба результата значимы на 5%.

6. **Какой канал лучший?**  
По profit proxy лучший `organic`. По paid conversion лучший `email`. Это разные вопросы.

7. **Где риск в оплате?**  
`mobile_web` имеет самый высокий payment failed rate: `7.0%`.

8. **Что бы ты сделал дальше?**  
Rollout onboarding, payment diagnostics для mobile web, CRM для activated non-payers, оптимизация paid каналов.

9. **Какие ограничения?**  
Синтетические данные, короткое revenue window, нет реального incremental marketing lift, нужны SRM/event QA.

10. **Почему этот проект хорош для портфолио?**  
Он показывает Python, SQL, статистику, A/B, продуктовую логику, BI-мышление и business recommendations.
