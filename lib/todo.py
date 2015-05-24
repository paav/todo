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

    def __repr__(self):
        out = '\n<Tag object>\n'
        for k, v in self._attrs.iteritems():
            out += '  %-10s%s\n' % (k + ':', v) 
        return out

    @property
    def attrs(self):
        return self._attrs

    @attrs.setter
    def attrs(self, attrs):
        # TODO: make in pythonic way
        for k, v in attrs.iteritems():
            if k in self._attrs:
                self._attrs[k] = attrs[k]


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
            'id':        '',
            'title':     '',
            'create_date': time.time(),
            'done_date': None,
            'body':      '',
            'priority':  0
        }
        self.attrs = attrs
        self._isnew = isnew

    def todict(self):
        vdict = self._attrs.copy()
        vdict['done_date'] = ''
        vdict['isnew'] = self._isnew
        vdict['tags'] = [ tag.todict() for tag in self._tags ]
        return vdict

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
    def done_date(self):
        return self._attrs['done_date']

    @done_date.setter
    def done_date(self, value):
        self._attrs['done_date'] = value

    @property
    def id(self):
        return self._attrs['id']

    def findall(self):
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

    def gettagnames(self):
        return [ tag.name for tag in self._tags ]

    def save(self):
        cur = self._dbcon.cursor()
        attrs = self.attrs.copy()
        pk = attrs['id']
        del attrs['id']
        if self.isnew:
            cols = ','.join(attrs.keys())
            values = ('?,' * len(attrs))[:-1]
            sql = 'INSERT INTO task (' + cols +') VALUES(' + values + ')'
            params = tuple(attrs.values()) 
        else:
            setclause = ','.join(map(lambda x: x + '=?', attrs.keys()))
            sql = 'UPDATE task SET ' + setclause + ' WHERE id=?'
            params = tuple(attrs.values() + [pk]) 
        cur.execute(sql, params) 
        self._dbcon.commit()
        if self.isnew:
            self._isnew = False
            pk = cur.lastrowid
            self._attrs['id'] = pk
        Tag().delall('task_id=?', (pk,))
        if self.tags:
            for tag in self.tags:
                tag.task_id = pk
            Tag().saveall(self.tags)

    @property
    def priority(self):
        return self._attrs['priority']

    @priority.setter
    def priority(self, value):
        # TODO: why priority is a str?
        curpri = int(self._attrs['priority'])
        if isinstance(value, basestring):
            value = (curpri + int(value) if value[0] in ['+', '-']
                else int(value))
        self._attrs['priority'] = max(0, value)

    def delbyid(self, id):
        cur = self._dbcon.cursor()
        sql = 'DELETE FROM task WHERE id=?'
        cur.execute(sql, (id,))
        self._dbcon.commit()
        Tag().delall('task_id=?', (id,))


class TaskList(object):
    def __init__(self):
        self._tasks = []
        self._filter = {}

    def load(self):
        self._tasks = Task().findall()

    @property
    def filter(self):
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value

    def filterby_tagnames(self, tasks, tagnames):
        return [ task for task in tasks if set(tagnames) <= set(task.gettagnames()) ]

    def tovimlist(self):
        tasks = self._tasks
        if self._filter:
            tasks = tasks[:]
            for k, v in self._filter.iteritems():
                tasks = getattr(self, 'filterby_' + k)(tasks, v)
        return self._createvimlist(tasks)

    @staticmethod
    def _createvimlist(tasks):
        return [ task.todict() for task in tasks ]

    def findbyid(self, id):
        return [task for task in self._tasks if task.id == id][0]

    def get(self, idx):
        return self._tasks[idx]

    def delete(self, idx):
        del self._tasks[idx]

    def delbyid(self, id):
        for i, task in enumerate(self._tasks):
            if task.id == id:
                del self._tasks[i]

    def add(self, task):
        self._tasks.append(task)


class Tag(Model):
    def __init__(self, attrs={}):
        super(Tag, self).__init__()
        self._attrs = {
            'name':     '',
            'task_id':  '',
        }
        # TODO: make in pythonic way
        for k, v in self._attrs.iteritems():
            if k in attrs:
                self._attrs[k] = attrs[k]

    @property
    def name(self):
        return self._attrs['name']

    @property
    def task_id(self):
        return self._attrs['task_id']

    @task_id.setter
    def task_id(self, value):
        self._attrs['task_id'] = value

    def todict(self):
        return self._attrs

    def createmany(self, attrslist):
        return [Tag({'name': attrs['name'], 'task_id': attrs['task_id']})
                for attrs in attrslist]

    def saveall(self, tags):
        cur = self._dbcon.cursor()
        sql = 'INSERT INTO tag (name,task_id) VALUES'
        params = []
        for tag in tags:
            sql += '(?,?),'
            params.extend([tag.name, tag.task_id])
        cur.execute(sql[:-1], tuple(params))
        self._dbcon.commit()

    def delall(self, cond, params):
        sql = 'DELETE FROM tag WHERE ' + cond
        self._dbcur.execute(sql, params)
        self._dbcon.commit()

    def findall(self, cond, params):
        sql = 'SELECT * FROM tag WHERE ' + cond
        self.dbcur.execute(sql, params)
        tags = []
        for row in self.dbcur.fetchall():
            tags.append(Tag(row['name'], row['id'], row['task_id']))
        return tags

tasklist = TaskList()
