
import os
from aiogram import types

async def save_and_parse_file(file: types.Document, user_id: str):
    ext = file.file_name.split('.')[-1]
    valid_exts = ['csv', 'xls', 'xlsx', 'docx', 'sql']
    if ext.lower() not in valid_exts:
        return None
    path = f"dbs/{user_id}_{file.file_name}"
    await file.download(destination_file=path)
    return path

def list_columns(filepath):
    import pandas as pd
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath, nrows=1)
    elif filepath.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(filepath, nrows=1)
    elif filepath.endswith('.sql'):
        return ['таблицы SQL (поиск по всем)']
    elif filepath.endswith('.docx'):
        return ['текст документа Word']
    else:
        return []
    return df.columns.tolist()
