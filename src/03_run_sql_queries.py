# -*- coding: utf-8 -*-
"""Run all saved SQL queries and print/save their answers."""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'processed' / 'studyflow.sqlite'
QUERIES = ROOT / 'sql' / 'queries'
ANSWERS = ROOT / 'sql' / 'answers'
ANSWERS.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB)
for query_path in sorted(QUERIES.glob('*.sql')):
    sql = query_path.read_text(encoding='utf-8')
    answer = pd.read_sql_query(sql, conn)
    out_path = ANSWERS / query_path.with_suffix('.csv').name
    answer.to_csv(out_path, index=False)
    print('\n---', query_path.name, '---')
    print(answer.head(12))
conn.close()
