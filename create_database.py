import sqlite3

conn = sqlite3.connect('database/app.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome TEXT NOT NULL,
    Email TEXT NOT NULL UNIQUE,
    Senha TEXT NOT NULL
)
''')

conn.commit()
conn.close()

print("Base de dados criada com sucesso.")
