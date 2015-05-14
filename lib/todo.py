# -*- coding: utf8 -*-
import sqlite3
from pprint import pprint
import time

# TODO: drop globals
DBFILE = None


def setdb(dbfile):
    global DBFILE
    DBFILE = dbfile


class Model(object):
    def __init__(self):
        self._dbcon = sqlite3.connect(DBFILE)
        self._dbcon.row_factory = sqlite3.Row
        self._dbcur = self._dbcon.cursor()

    @property
    def attrs(self):
        return self._attrs

    @attrs.setter
    def attrs(self, value):
        self._attrs.update(value)

    @property
    def DBFILE(cls):
        return cls._DBFILE

class Task(Model):
    def __init__(self, attrs={}, isnew=True, tags=[]):
        super(Task, self).__init__()
        # attrs['tags'] from vim is a list of dicts, not Tag objects
        try:
            for i, tag in enumerate(tags):
                if isinstance(tag, dict):
                    tags[i] = Tag(tag)
        except KeyError:
            pass
        self._tags = tags
        # isnew from vim is a string like '0' or '1' 
        if not isinstance(isnew, bool):
            isnew = bool(int(isnew))
        self._attrs = {
            'id':        None,
            'title':     '',
            'create_date': time.time(),
            'body':      '',
            'priority':  0
        }
        # TODO: make in pythonic way
        for k, v in self._attrs.iteritems():
            if k in attrs:
                self._attrs[k] = attrs[k]
        self._isnew = isnew

    @property
    def isnew(self):
        return self._isnew

    @isnew.setter
    def isnew(self, value):
        self._isnew = value

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        self._tags = value

    @property
    def id(self):
        return self._attrs['id']

    def findAll(self):
        cur = self._dbcur
        sql = 'SELECT * FROM task WHERE done_date IS NULL ORDER BY priority DESC'
        tagsql =  'SELECT * FROM tag WHERE task_id=?'
        tasks = []
        cur.execute(sql)
        for row in cur.fetchall():
            attrs = self._rowtoattrs(row)
            task = Task(attrs)
            tags = []
            cur.execute(tagsql, (task.id,))
            for tagrow in cur.fetchall():
                attrs = self._rowtoattrs(tagrow)
                tags.append(Tag(attrs))
            task.tags = tags
            task.isnew = False
            tasks.append(task)
        return tasks

    @staticmethod
    def _rowtoattrs(row):
        """Converts sqlite3.Row to attrs dict."""
        return dict(zip(row.keys(), list(row)))

    def _findAll(self, cond='', params=()):
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
        pass

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


class TaskList:
    def __init__(self):
        self.cond = ''
        self.params = ()
        self.last_task_at_cursor = None
        self.tbody_1strow_lnum = 1
        self.filter_by_tags = []
        # self.populate() 

    def gettasks(self):
        tasks = []
        for task in Task().findAll():
            attrs = self._convnone(task.attrs)
            tags = []
            for tag in task.tags: 
                tags.append(self._convnone(tag.attrs))
            attrs['tags'] = tags
            attrs['isnew'] = task.isnew
            tasks.append(attrs)
        return tasks

    @staticmethod
    def _convnone(attrs):
        for k, v in attrs.iteritems():
            if v is None: 
                attrs[k] = ''
        return attrs

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


class Tag(Model):
    def __init__(self, attrs={}):
        super(Tag, self).__init__()
        self._attrs = {
            'id':       None,
            'name':     '',
            'task_id':  None,
        }
        self._attrs.update(attrs)

    @property
    def name(self):
        return self._attrs['name']

    @property
    def task_id(self):
        return self._attrs['task_id']

    def save(self):
        pass
        
    def deleteAll(self, cond, params):
        pass

    def findAll(self, cond, params):
        sql = 'SELECT * FROM tag WHERE ' + cond
        self.dbcur.execute(sql, params)
        tags = []
        for row in self.dbcur.fetchall():
            tags.append(Tag(row['name'], row['id'], row['task_id']))
        return tags

tasklist = TaskList()
