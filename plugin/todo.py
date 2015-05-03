import vim
import sqlite3
from datetime import datetime
import time

BUFF_MAIN = 'Todo'

db = vim.eval('s:db')
conn = sqlite3.connect(db)
cur = conn.cursor()

def renderTasks():
    gotoWinWithBufferName(BUFF_MAIN)
    vim.command('setlocal modifiable')
    vim.current.buffer[:] = None

    header = "%-5s%-18s%-40s%-10s" % ('id', 'Created', 'Title', 'Priority')
    vim.current.buffer.append(header)

    for row in cur.execute('SELECT * FROM task'):
        id, title, createDate, priority = row[0], row[1], row[3], row[6]

        oCreateDate = datetime.fromtimestamp(createDate)

        line = "%-5d%-18s%-40s%-10s" % (id, oCreateDate.strftime('%Y-%m-%d'), title, priority)
        vim.current.buffer.append(line)

    vim.command('setlocal nomodifiable')

def saveTask():
    title = vim.current.buffer[0]
    body = vim.current.buffer[1]
    timestamp = time.time()
    priority = 0;

    sql = "INSERT INTO task (title,body,create_date,priority) VALUES(?,?,?,?)"

    cur.execute(sql, (title, body, timestamp, priority))
    conn.commit()

    renderTasks()

def deleteTask():
    curLineNum = vim.current.window.cursor[0]
    buffer = vim.current.buffer
    
    curLine = buffer[curLineNum - 1]

    id = curLine.split(None, 1)[0]
    print(id)

    sql = "DELETE FROM task WHERE id=?"

    cur.execute(sql, (id,))
    conn.commit()

    renderTasks()

def getBuffByName(buffName):
    buffNum = vim.eval('bufnr("%s")' % buffName)

    return vim.buffers[buffNum]

def gotoWinWithBufferName(buffName):
    buffNum = vim.eval('bufnr("%s")' % buffName)

    winNum = int(vim.eval('bufwinnr(%d)' % int(buffNum)))
    vim.command('%dwincmd w' % winNum)
