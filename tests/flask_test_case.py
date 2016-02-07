# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os
import random
import string
import unittest

from flask import Flask
from sqlalchemy.engine.url import make_url

from woodbox.db import db


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        # FIXME: find a way to configure the db to test other backends (like MySQL).
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['PASSWORD_SALT'] = 'salt'
        self.app.config['TESTING'] = True
        db.init_app(self.app)

    def tearDown(self):
        with self.app.test_request_context('/'):
            if db.engine.driver == 'pysqlite':
                url = make_url(self.app.config['SQLALCHEMY_DATABASE_URI'])
                if url.database is not None:
                    os.remove(url.database)

    @staticmethod
    def str_n(n):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))
