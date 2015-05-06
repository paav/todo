import vim
import sqlite3
from datetime import datetime
import time

# TODO: make something with this
BUFNAME_MAIN = 'Todo'
BUFNAME_EDIT = 'TodoEdit'
DBFILE = vim.eval('s:db')

task_list = TaskList()
cur_task = None
vimc = Vim()

def render_tasks():
    task_list.render()

def save():
    attrs = parse_task_attrs()
    if not attrs:
        return
    if cur_task:
        cur_task.attrs = attrs
        cur_task.save()
    else:
        Task(attrs, isnew=True).save()
    task_list.render()

def delete():
    task = task_list.get_task_at_cursor()
    task.delete()
    task_list.render()

def add():
    vimc.open_edit_win()

def edit():
    global cur_task
    cur_task = task_list.get_task_at_cursor()
    if not cur_task:
        return
    print(cur_task.isnew)
    cur_task.edit()

def priority_add(num):
    """Increase/decrease task priority by 1."""
    task = Task.instance().findById(get_id()) 
    task.setAttr('priority', task.getAttr('priority') + num)
    task.save()
    render_tasks()

def parse_task_attrs():
    buf = vimc.get_buffer(BUFNAME_EDIT)
    if not buf[0]:
        return {}
    title = buf[0]
    body = '\n'.join(buf[1:])
    return {'title': title, 'body': body}

def get_id():
    line = vim.current.line
    return line.split(None, 1)[0]

def get_priority():
    line = vim.current.line
    return line.split()[-1]

def get_buffer(bufname):
    bufnr = int(vim.eval('bufnr("%s")' % bufname))
    return vim.buffers[bufnr]


class Vim:        
    def __init__(self):
        self.bufmain = 'Todo'
        self.bufedit = 'TodoEdit'

    def write(self, lines):
        buf = vim.current.buffer
        opt_save = buf.options['modifiable']
        buf.options['modifiable'] = True
        # vim.current.buffer = self.get_buffer(self.bufmain)
        # vim.command('setlocal modifiable')
        vim.current.buffer[:] = None
        vim.current.buffer[:] = lines
        if self.is_writable(buf):
            vim.command('w')
        buf.options['modifiable'] = opt_save

    @staticmethod
    def is_writable(buf):
        return not buf.options['buftype']

    @staticmethod
    def get_buffer(bufname):
        bufnr = int(vim.eval('bufnr("%s",%d)' % (bufname, 1)))
        return vim.buffers[bufnr]

    def get_line_number(self):
        return (vim.current.window.cursor)[0]

    def open_main_win(self):
        vim.current.buffer = self.get_buffer(self.bufmain)

    def open_edit_win(self):
        vim.command('new %s' % self.bufedit)
        self.clear_buf()

    def clear_buf(self):
        vim.current.buffer[:] = None
        vim.command('write')


class TaskList:

    def __init__(self):
        self.vim = Vim()
        self.populate() 

    def populate(self):
        self.tasks = Task.instance().findAll()

    def render(self):
        self.vim.open_main_win()
        self.vim.write(self.create_table())

    def create_table(self):
        # TODO: rewrite this
        self.populate()
        attributes = self.tasks[0].getAttributes()
        keys = attributes.keys()
        colnames = dict(zip(keys, keys))
        format = '%(id)-5s%(create_date)-18s%(title)-40s%(priority)-10s'
        lHeader = [format % colnames, '-' * 73]
        lBody = []
        for task in self.tasks:
            lBody.append(format % task.getAttributes())
        lTable = lHeader + lBody
        return lTable;

    def get_task_at_cursor(self):
        lnum = self.vim.get_line_number()
        if lnum < 3:
            return None
        return self.tasks[lnum - 3]


class Task(object):
    def __init__(self, attrs, dbconn=None, isnew=False):
        self.dbconn = Db.connection()
        self.dbcur = self.dbconn.cursor()
        self._attrs = {
            'id':           None,
            'title':        '',
            'body':         '',
            'create_date':  time.time(),
            'priority':     0
        }
        self._attrs.update(attrs)
        self._isnew = isnew
        self.vim = Vim()

    @property
    def isnew(self):
        return self._isnew

    @isnew.setter
    def isnew(self, value):
        self._isnew = value

    @property
    def attrs(self):
        return self._attrs

    @attrs.setter
    def attrs(self, value):
        self._attrs.update(value)

    @classmethod
    def instance(cls):
        return cls({})

    def getAttributes(self):
        return self._attrs 

    def findAll(self):
        cur = self.dbconn.cursor()

        sql = 'SELECT * FROM task ORDER BY priority DESC'
        cur.execute(sql)

        tasks = []

        for row in cur.fetchall():
            attrs = dict(zip(row.keys(), list(row)))
            tasks.append(Task(attrs, isnew=False))

        return tasks

    def findById(self, id):
        cur = self.dbconn.cursor()
        sql = 'SELECT * FROM task WHERE id=?'
        cur.execute(sql, (id,))
        task = Task(Task.row2attrs(cur.fetchone()), isnew=False)
        return task

    @staticmethod
    def row2attrs(row):
        """Convert sqlite3.Row to attrs dict."""
        return dict(zip(row.keys(), list(row)))

    def save(self):
        cur = self.dbconn.cursor()
        attrs = self.attrs
        print(self.isnew)
        if not self.isnew:
            sqlpart = ','.join(map(lambda x: x + '=?', attrs.keys()))
            sql = 'UPDATE task SET ' + sqlpart + ' WHERE id=?'
            params = tuple(attrs.values() + [attrs['id']]) 
        else:
            columns = ','.join(attrs.keys())
            pholders = ('?,' * len(attrs))[:-1]
            sql = 'INSERT INTO task (' + columns +') VALUES(' + pholders + ')'
            params = tuple(attrs.values()) 
        cur.execute(sql, params) 
        self.dbconn.commit()

    def delete(self):
        self.deleteById(self.getAttr('id'))

    def deleteById(self, id):
        cur = self.dbconn.cursor()
        sql = 'DELETE FROM task WHERE id=?'

        cur.execute(sql, (id,))
        self.dbconn.commit()

    def getAttr(self, name):
        return self.attrs[name]

    def setAttr(self, name, value):
        self.attrs[name] = value

    def edit(self):
        lines = [self.attrs['title']] + self.attrs['body'].split('\n')
        self.vim.open_edit_win()
        self.vim.write(lines)


class Db:
    def __init__(self):
        conn = sqlite3.connect(DBFILE)
        conn.row_factory = sqlite3.Row
        self.conn = conn

    @classmethod
    def connection(cls):
        return cls().conn
