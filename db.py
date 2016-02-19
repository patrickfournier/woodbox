# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os

import sqlalchemy

from flask import _app_ctx_stack

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.engine import reflection
from sqlalchemy.schema import (
    MetaData,
    Table,
    DropTable,
    ForeignKeyConstraint,
    DropConstraint,
)
from sqlalchemy.engine.url import make_url

class Database(SQLAlchemy):
    def __init__(self, *kargs, **kwargs):
        self.initializers = list()
        super(Database, self).__init__(*kargs, **kwargs)

    def register_initializer(self, initializer):
        self.initializers.append(initializer)

    def initialize(self):
        if self.app is not None:
            app = self.app
        else:
            ctx = _app_ctx_stack.top
            if ctx is not None:
                app = ctx.app

        Database.drop_all(app.config['SQLALCHEMY_DATABASE_URI'])
        self.create_all()
        for i in self.initializers:
            i().do_init()

    @staticmethod
    def drop_all(db_url=None):
        if db_url is None:
            db_url = os.getenv('WOODBOX_DATABASE_URI', 'sqlite+pysqlite://')
        info = make_url(db_url)
        engine = sqlalchemy.create_engine(info)

        conn = engine.connect()
        trans = conn.begin()
        try:
            inspector = reflection.Inspector.from_engine(engine)
            metadata = MetaData()
            tbs = []
            all_fks = []
            for table_name in inspector.get_table_names():
                fks = []
                for fk in inspector.get_foreign_keys(table_name):
                    if not fk['name']:
                        continue
                    fks.append(
                        ForeignKeyConstraint((),(),name=fk['name'])
                    )
                t = Table(table_name,metadata,*fks)
                tbs.append(t)
                all_fks.extend(fks)


            for fkc in all_fks:
                conn.execute(DropConstraint(fkc))
            for table in tbs:
                conn.execute(DropTable(table))

            trans.commit()
        except Exception as e:
            trans.rollback()
            raise
        finally:
            conn.close()

db = Database()

class DatabaseInitializerMetaclass(type):
    def __init__(cls, name, bases, dct):
        db.register_initializer(cls)

class DatabaseInitializer(object):
    __metaclass__ = DatabaseInitializerMetaclass

    def do_init(self):
        pass
