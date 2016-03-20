# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os
import types

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

    def register_initializer(self, initializer, dependencies):
        self.initializers.append((initializer, set(dependencies)))

    # TODO: add a test.
    def sorted_initializers(self):
        """Perform a topological sort on initializers.

        Reference: http://stackoverflow.com/questions/11557241/python-sorting-a-dependency-list
        """
        pending = [(name, set(deps)) for name, deps in self.initializers] # copy deps so we can modify set in-place
        emitted = []
        while pending:
            next_pending = []
            next_emitted = []
            for entry in pending:
                name, deps = entry
                deps.difference_update(emitted) # remove deps we emitted last pass
                if deps: # still has deps? recheck during next pass
                    next_pending.append(entry)
                else: # no more deps? time to emit
                    yield name
                    emitted.append(name) # <-- not required, but helps preserve original ordering
                    next_emitted.append(name) # remember what we emitted for difference_update() in next pass
            if not next_emitted: # all entries have unmet deps, one of two things is wrong...
                raise ValueError("Cyclic or missing dependancy detected: {0}".format(next_pending))
            pending = next_pending
            emitted = next_emitted

    def initialize(self):
        if self.app is not None:
            app = self.app
        else:
            ctx = _app_ctx_stack.top
            if ctx is not None:
                app = ctx.app

        Database.drop_all(app.config['SQLALCHEMY_DATABASE_URI'])
        self.create_all()
        for i in self.sorted_initializers():
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
        db.register_initializer(cls, cls.dependencies)

class DatabaseInitializer(object):
    __metaclass__ = DatabaseInitializerMetaclass

    dependencies = []

    def do_init(self):
        pass


# Patch db.Model class to add precondition checks.
# Create precondition check should be done in constructor.
def checkUpdatePrecondition(s):
    pass
db.Model.checkUpdatePrecondition = types.MethodType(checkUpdatePrecondition, db.Model)

def checkDeletePrecondition(s):
    pass
db.Model.checkDeletePrecondition = types.MethodType(checkDeletePrecondition, db.Model)
