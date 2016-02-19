# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os
import random
import string
import unittest
import warnings

import sqlalchemy

from flask import Flask
from sqlalchemy.engine.url import make_url
from sqlalchemy_utils.functions import create_database, drop_database, database_exists
from woodbox.db import db


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        # Example URI:
        # - sqlite+pysqlite:////tmp/test.sqlite
        # - mysql+mysqldb://woodbox_test:woodbox_test@localhost/woodbox_test
        # - postgresql+psycopg2://woodbox_test:woodbox_test@localhost/woodbox_test
        self.app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('WOODBOX_DATABASE_URI', 'sqlite+pysqlite://')
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['PASSWORD_SALT'] = 'salt'
        self.app.config['TESTING'] = True

        if self.app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite+pysqlite://' \
        and not database_exists(self.app.config['SQLALCHEMY_DATABASE_URI']):
            create_database(self.app.config['SQLALCHEMY_DATABASE_URI'])

        db.init_app(self.app)

        if self.app.config['SQLALCHEMY_DATABASE_URI'][:5] == 'mysql':
            # Make MySQL warnings raise exceptions.
            warnings.simplefilter('error')

    def tearDown(self):
        if self.app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite+pysqlite://':
            # Dropping the database is necessary for postgresql, in order
            # to reset the autoincrement counters.
            drop_database(self.app.config['SQLALCHEMY_DATABASE_URI'])

    @staticmethod
    def str_n(n):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))
