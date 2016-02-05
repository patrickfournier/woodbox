# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from flask.ext.sqlalchemy import SQLAlchemy

class Database(SQLAlchemy):
    def __init__(self, *kargs, **kwargs):
        self.initializers = list()
        super(Database, self).__init__(*kargs, **kwargs)

    def register_initializer(self, initializer):
        self.initializers.append(initializer)

    def initialize(self):
        db.drop_all()
        db.create_all()
        for i in self.initializers:
            i.do_init()

db = Database()

class DatabaseInitializerMetaclass(type):
    def __init__(cls, name, bases, dct):
        db.register_initializer(cls())

class DatabaseInitializer(object):
    __metaclass__ = DatabaseInitializerMetaclass

    def do_init(self):
        pass
