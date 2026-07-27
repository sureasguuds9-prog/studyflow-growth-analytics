SELECT topic,
       COUNT(*) AS tickets,
       AVG(resolution_hours) AS avg_resolution_hours,
       AVG(csat) AS avg_csat,
       SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) AS high_priority_tickets
FROM support_tickets
GROUP BY topic
ORDER BY tickets DESC;
