import vim
import sqlite3
from datetime import datetime
import time

# TODO: make something with this
BUF_MAIN = 'Todo'
DATABASE = vim.eval('s:db')

class Db:
    def __init__(self):
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        self.conn = conn

    @classmethod
    def connection(cls):
        return cls().conn


def render_tasks():
    vim.current.buffer = get_buffer(BUF_MAIN)
    vim.command('setlocal modifiable')
    vim.current.buffer[:] = None

    tasks = Task.instance().findAll()

    # TODO: make something with this
    def formatDateTime(task):
       task.setAttr('create_date', datetime.fromtimestamp(
           task.getAttr('create_date')).strftime('%Y-%m-%d'))
       return task

    tasks = map(formatDateTime, tasks)

    vim.current.buffer.append(create_tasks_table(tasks))
    vim.command('setlocal nomodifiable')

def create_tasks_table(tasks):
    attributes = tasks[0].getAttributes()
    keys = attributes.keys()
    colnames = dict(zip(keys, keys))
    format = '%(id)-5s%(create_date)-18s%(title)-40s%(priority)-10s'

    lHeader = [format % colnames, '-' * 73]
    lBody = []

    for task in tasks:
        lBody.append(format % task.getAttributes())

    lTable = lHeader + lBody
    return lTable;

def saveTask():
    title = vim.current.buffer[0]
    body = '\n'.join(vim.current.buffer[1:])
    
    Task({'title': title,
          'body': body}).save()

    render_tasks()

def deleteTask():
    line = vim.current.line
    id = line.split(None, 1)[0]
    print(id)

    Task.instance().deleteById(id)

    render_tasks()

def getBuffByName(buffName):
    buffNum = vim.eval('bufnr("%s")' % buffName)

    return vim.buffers[buffNum]

def gotoWinWithBufferName(buffName):
    buffNum = vim.eval('bufnr("%s")' % buffName)

    winNum = int(vim.eval('bufwinnr(%d)' % int(buffNum)))
    vim.command('%dwincmd w' % winNum)

def get_buffer(bufname):
    bufnr = int(vim.eval('bufnr("%s")' % bufname))

    return vim.buffers[bufnr]
        
class Task:

    def __init__(self, attributes, dbconn = None):
        self.dbconn = Db.connection()

        self.attributes = {
            'id':           None,
            'title':        '',
            'body':         '',
            'create_date':  time.time(),
            'priority':     0
        }

        self.attributes.update(attributes)

    @classmethod
    def instance(cls):
        return cls({})

    def getAttributes(self):
        return self.attributes 

    def findAll(self):
        cur = self.dbconn.cursor()

        sql = 'SELECT * FROM task'
        cur.execute(sql)

        tasks = []

        for row in cur.fetchall():
            attrs = dict(zip(row.keys(), list(row)))
            tasks.append(Task(attrs))

        return tasks

    def save(self):
        cur = self.dbconn.cursor()

        attrs = self.attributes
        columns = ','.join(attrs.keys())
        pholders = ('?,' * len(attrs))[:-1]

        sql = 'INSERT INTO task (' + columns +') VALUES(' + pholders + ')'
        params = tuple(attrs.values())

        cur.execute(sql, params) 
        self.dbconn.commit()

    def deleteById(self, id):
        cur = self.dbconn.cursor()
        sql = 'DELETE FROM task WHERE id=?'

        cur.execute(sql, (id,))
        self.dbconn.commit()

    def getAttr(self, name):
        return self.attributes[name]

    def setAttr(self, name, value):
        self.attributes[name] = value
