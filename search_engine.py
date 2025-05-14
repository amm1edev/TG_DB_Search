import pandas as pd
import os

def search_in_dbs(query):
    results = []
    for file in os.listdir("dbs/"):
        path = os.path.join("dbs", file)
        try:
            if file.endswith('.csv'):
                try:
                    df = pd.read_csv(path)
                except:
                    df = pd.read_csv(path, sep=':', header=None)

            elif file.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(path)

            elif file.endswith('.docx'):
                from docx import Document
                doc = Document(path)
                text = '\n'.join(p.text for p in doc.paragraphs)
                if query.lower() in text.lower():
                    results.append(f"📄 Совпадение в {file}:\n{text[:1000]}...")
                continue

            elif file.endswith('.sql'):
                import sqlite3
                conn = sqlite3.connect(path)
                for table in pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)["name"]:
                    df = pd.read_sql(f"SELECT * FROM {table}", conn)
                    matches = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)]
                    if not matches.empty:
                        formatted = format_matches(matches)
                        results.append(f"🗄 Совпадение в {file}, таблица {table}:\n{formatted}")
                continue

            else:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                    if query.lower() in text.lower():
                        results.append(f"📄 Совпадение в {file}:\n{text[:1000]}...")
                continue

            matches = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)]
            if not matches.empty:
                formatted = format_matches(matches)
                results.append(f"📄 Совпадение в {file}:\n{formatted}")

        except Exception:
            continue
    return results

def search_in_column(column, value):
    results = []
    for file in os.listdir("dbs/"):
        path = os.path.join("dbs", file)
        try:
            df = pd.read_csv(path, sep=None, engine='python')
            if column not in df.columns:
                continue
            matches = df[df[column].astype(str).str.contains(value, case=False)]
            if not matches.empty:
                formatted = format_matches(matches)
                results.append(f"📄 В {file}, столбец {column}:\n{formatted}")
        except Exception:
            continue
    return results

def format_matches(matches):
    lines = []
    for _, row in matches.iterrows():
        formatted_row = "\n".join([f"<b>{col}</b>: <code>{str(val)}</code>" for col, val in row.items()])
        lines.append(f"=---------------=\n{formatted_row}")
    return "\n\n".join(lines)
