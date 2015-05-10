# -*- coding: utf8 -*-
import vim
import sqlite3
from datetime import datetime
import time

# TODO: make something with this
BUFNAME_MAIN = 'Todo'
BUFNAME_EDIT = 'TodoEdit'
DBFILE = vim.eval('s:db')
TAG_MARK = '#'
MSG_TIP ="""\
"Press ? for help
"""

MSG_HELP ="""\
"k: move cursor up
"j: move cursor down 
"n: new task
"e: edit task
"d: delete task
"f: filter tasks by tags
"=: raise priority
"-: drop priority
"?: toggle help\
"""

help_isvisible = False

cur_task = None

def toggle_help():
    global help_isvisible
    buf = vim.current.buffer
    opt_save = buf.options['modifiable']
    buf.options['modifiable'] = True
    if help_isvisible:
        buf[0:10] = None
        help_isvisible = False    
        buf.append(MSG_TIP.split('\n'), 0)
    else:
        buf[0:1] = None
        buf.append(MSG_HELP.split('\n'), 0)
        help_isvisible = True    
    buf.options['modifiable'] = opt_save

def render_tasks():
    vimc.open_main_win()
    vimc.write(MSG_TIP.split('\n'))
    task_list.render()

def save():
    global cur_task
    attrs = parse_task_attrs()
    tags = parse_tags()
    if attrs:
        if cur_task:
            cur_task.attrs = attrs
            cur_task.save()
            task_id = cur_task.getAttr('id')
            cur_task = None
        else:
            newtask = Task(attrs, isnew=True)
            newtask.save()
            task_id = newtask.getAttr('id')
            task_list.last_task_at_cursor = newtask
        Tag.inst().deleteAll('task_id=?', (task_id,))
        if tags:
            for tag in tags:
                tag.task_id = task_id
                tag.save()
    task_list.render()

def refresh():
    task_list.render()

def delete():
    task = task_list.get_task_at_cursor()
    cursor_save = task_list.get_cursor()
    task.delete()
    task_list.render()
    try:
        task_list.set_cursor(cursor_save)
    except:
        task_list.set_cursor(cursor_save - 1)

def add():
    vimc.open_edit_win()

def finish():
    # TODO: repetitive code
    task = task_list.get_task_at_cursor()
    cursor_save = task_list.get_cursor()
    task.finish()
    task_list.render()
    try:
        task_list.set_cursor(cursor_save)
    except:
        task_list.set_cursor(cursor_save - 1)

def edit():
    global cur_task
    cur_task = task_list.get_task_at_cursor()
    if not cur_task:
        return
    cur_task.edit()

def priority_add(num):
    """Increase/decrease task priority by 1."""
    task = task_list.get_task_at_cursor()
    task.setAttr('priority', task.getAttr('priority') + num)
    task.save()
    task_list.render()

def apply_tag_filter():
    msg = 'Filter by tags: '
    vim.command('let str_tags = input("%s")' % msg)
    str_tags = vim.eval('str_tags')
    task_list.apply_tag_filter(str_tags.split())

def parse_task_attrs():
    buf = vimc.get_buffer(BUFNAME_EDIT)
    if not buf[0]:
        return {}
    title = buf[0]
    body = '\n'.join(buf[1:])
    return {'title': title, 'body': body}

def parse_tags():
    buf = vimc.get_buffer(BUFNAME_EDIT)
    last_line = buf[-1]
    if last_line[0] != TAG_MARK:
        return
    str_tags = last_line[1:]
    names = str_tags.split()
    if not names:
        return
    tags = []
    for name in names:
        tags.append(Tag(name=name))
    return tags

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

    def write(self, lines, offset=0):
        buf = vim.current.buffer
        opt_save = buf.options['modifiable']
        buf.options['modifiable'] = True
        vim.current.buffer[offset:] = None
        vim.current.buffer[offset:] = lines
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

    def win_width(self):
        return vim.current.window.width - 1

    def open_edit_win(self):
        vim.command('new %s' % self.bufedit)
        self.clear_buf()

    def clear_buf(self):
        vim.current.buffer[:] = None
        vim.command('write')

    def set_cursor(self, row):
        vim.current.window.cursor = (row, 1)

    def get_cursor(self):
        return (vim.current.window.cursor)[0]


class TaskList:

    def __init__(self):
        self.vim = Vim()
        self.cond = ''
        self.params = ()
        self.last_task_at_cursor = None
        self.tbody_1strow_lnum = 1
        self.filter_by_tags = []
        self.populate() 

    def populate(self):
        self.tasks = Task.inst().findAll(self.cond, self.params)

    def render(self):
        self.vim.open_main_win()
        self.vim.write(self.create_table(), offset=2)
        if self.last_task_at_cursor:
            lnum = self.last_task_lnum()
        else:
            lnum = self.tbody_1strow_lnum 
        self.vim.set_cursor(lnum)

    def apply_tag_filter(self, tags):
        if tags:
            cond = ' and '.join(['name=?'] * len(tags))
            tags = Tag.inst().findAll(cond, tuple(tags)) 
            task_ids = map(lambda t: t.task_id, tags)
            self.cond = 'id IN(' + ','.join(['?'] * len(task_ids)) + ')'
            self.params = tuple(task_ids)
        else:
            self.cond = ''
            self.params = ()
        self.render()

    def create_table(self):
        self.populate()
        labels = Task.inst().attr_labels()
        labels['tag'] = 'Tag'
        format = '%(create_date)-10s%(title)-37s%(tag)-12s%(priority)-s'
        # Add ~ for table head highlighting
        thead = '~' + format % labels 
        tdelim = '─' * self.vim.win_width() 
        tbody_lines = []
        # TODO: do something with 5
        self.tbody_1strow_lnum = 5
        for task in self.tasks:
            # TODO: drop copy() from here
            fields = task.attrs.copy()
            try:
                fields['tag'] = task.tag_names()[0]
            except IndexError:
                fields['tag'] = ''
            # Add ` for row cell highlighting
            pri = fields['priority']
            pri_pfx = ''
            if pri > 5:
                pri_pfx = '!1'
            elif pri > 2:
                pri_pfx = '!2'
            tbody_lines.append('`' + pri_pfx + format % self.format_attrs(fields)) 
        table_lines = [thead, tdelim] + tbody_lines
        return table_lines

    @classmethod
    def format_attrs(cls, attrs):
        attrs['create_date'], = cls.format_dates(attrs['create_date'])
        return attrs

    @staticmethod
    def format_dates(*tstamps):
        def format_date(tstamp):
            # %-d -- works only for unix like os
            return unicode(datetime.fromtimestamp(tstamp).strftime('%-d %b'),
                           'utf8') 
        return map(format_date, tstamps)

    def get_task_at_cursor(self):
        lnum = self.vim.get_line_number()
        if lnum < self.tbody_1strow_lnum:
            return None
        task = self.tasks[lnum - self.tbody_1strow_lnum]
        self.last_task_at_cursor = task
        return task 

    def last_task_lnum(self):
        last_task = self.last_task_at_cursor
        try:
            return self.get_index_of_task(last_task) + self.tbody_1strow_lnum
        except ValueError:
            return self.tbody_1strow_lnum

    def get_index_of_task(self, task):
        id = task.getAttr('id')
        for i, t in enumerate(self.tasks):
            if t.getAttr('id') == id:
                return i
        raise ValueError

    def get_cursor(self):
        return self.vim.get_cursor()

    def set_cursor(self, lnum):
        return self.vim.set_cursor(lnum)

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
    def inst(cls):
        return cls({})

    def attr_labels(self):
        custom = {
            'title': 'Title',
            'create_date': 'Created',
            'priority': 'Pri'
        }
        labels = self._default_labels()
        labels.update(custom)
        return labels 

    def _default_labels(self):
        keys = self._attrs.keys()
        return dict(zip(keys, keys))

    def findAll(self, cond='', params=()):
        cur = self.dbconn.cursor()
        sql = 'SELECT * FROM task WHERE done_date IS NULL'
        if cond:
            sql += ' AND %s ' % cond
        sql +=  ' ORDER BY priority DESC'
        cur.execute(sql, params)
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

    def tag_names(self):
        sql = 'SELECT * FROM tag WHERE task_id=?'
        self.dbcur.execute(sql, (self.getAttr('id'),))
        tag_names = []
        for row in self.dbcur.fetchall():
            tag_names.append(row['name'])
        return tag_names

    @staticmethod
    def row2attrs(row):
        """Convert sqlite3.Row to attrs dict."""
        return dict(zip(row.keys(), list(row)))

    def save(self):
        cur = self.dbconn.cursor()
        attrs = self.attrs
        if self.isnew:
            columns = ','.join(attrs.keys())
            pholders = ('?,' * len(attrs))[:-1]
            sql = 'INSERT INTO task (' + columns +') VALUES(' + pholders + ')'
            params = tuple(attrs.values()) 
        else:
            sqlpart = ','.join(map(lambda x: x + '=?', attrs.keys()))
            sql = 'UPDATE task SET ' + sqlpart + ' WHERE id=?'
            params = tuple(attrs.values() + [attrs['id']]) 
        cur.execute(sql, params) 
        if cur.lastrowid:
            self.setAttr('id', cur.lastrowid)
        self.dbconn.commit()

    def delete(self):
        self.deleteById(self.getAttr('id'))

    def deleteById(self, id):
        cur = self.dbconn.cursor()
        sql = 'DELETE FROM task WHERE id=?'

        cur.execute(sql, (id,))
        self.dbconn.commit()

    def getAttr(self, name):
        return self._attrs[name]

    def setAttr(self, name, value):
        self._attrs[name] = value

    def edit(self):
        lines = []
        lines.append(self.attrs['title'])
        if self.getAttr('body'):
            lines.extend(self.attrs['body'].split('\n'))
        self.vim.open_edit_win()
        self.vim.write(lines)

    def finish(self):
        sql = 'UPDATE task SET done_date=? WHERE id=?'
        self.dbcur.execute(sql, (time.time(), self.getAttr('id')))
        self.dbconn.commit()


class Tag:
    def __init__(self, name, id=None, task_id=None):
        self.id = id
        self.name = name
        self.task_id = task_id
        self.dbconn = Db.connection()
        self.dbcur = self.dbconn.cursor()

    @classmethod
    def inst(cls):
        return cls({})

    def save(self):
        sql = 'INSERT INTO tag (name,task_id) VALUES(?,?)'
        self.dbcur.execute(sql, (self.name, self.task_id))
        self.dbconn.commit()
        
    def deleteAll(self, cond, params):
        sql = 'DELETE FROM tag WHERE ' + cond
        self.dbcur.execute(sql, params)
        self.dbconn.commit()

    def findAll(self, cond, params):
        sql = 'SELECT * FROM tag WHERE ' + cond
        self.dbcur.execute(sql, params)
        tags = []
        for row in self.dbcur.fetchall():
            tags.append(Tag(row['name'], row['id'], row['task_id']))
        return tags

class Db:
    def __init__(self):
        conn = sqlite3.connect(DBFILE)
        conn.row_factory = sqlite3.Row
        self.conn = conn

    @classmethod
    def connection(cls):
        return cls().conn

task_list = TaskList()
vimc = Vim()
