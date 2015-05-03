import vim
import sqlite3

conn = sqlite3.connect('../data/todo.db')
cur = conn.cursor()

def renderTasks():
    vim.command('setlocal modifiable')
    vim.current.buffer[:] = None

    for row in c.execute('SELECT * FROM task'):
        vim.current.buffer.append(row[1] + row[2])

    vim.command('setlocal nomodifiable')
