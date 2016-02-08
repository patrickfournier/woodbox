# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os
import random
import string
import unittest
import warnings

import os

from flask import Flask
from sqlalchemy.engine.url import make_url

from woodbox.db import db


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        # Example URI:
        # - sqlite+pysqlite:////tmp/test.sqlite
        # - mysql+mysqldb://woodbox_test:woodbox_test@localhost/woodbox_test
        self.app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('WOODBOX_DATABASE_URI', 'sqlite+pysqlite://')
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['PASSWORD_SALT'] = 'salt'
        self.app.config['TESTING'] = True
        db.init_app(self.app)

        if self.app.config['SQLALCHEMY_DATABASE_URI'][:5] == 'mysql':
            warnings.simplefilter('error')

    def tearDown(self):
        with self.app.test_request_context('/'):
            if db.engine.name == 'sqlite':
                url = make_url(self.app.config['SQLALCHEMY_DATABASE_URI'])
                if url.database is not None:
                    os.remove(url.database)

    @staticmethod
    def str_n(n):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))
