#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os
from werkzeug.contrib.fixers import ProxyFix
from flask.ext.script import Manager, Shell, Command

from app import create_app, init_db

app = create_app()

app.wsgi_app = ProxyFix(app.wsgi_app)
# CAUTION: It is a security issue to use this middleware in a non-proxy setup
# because it will blindly trust the incoming headers which might be forged by
# malicious clients.
# Ref: http://flask.pocoo.org/docs/0.10/deploying/wsgi-standalone/#proxy-setups

manager = Manager(app)

class InitDB(Command):
    def run(self):
        init_db()

def make_shell_context():
    return dict(app=app)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('init_db', InitDB())

if __name__ == '__main__':
    manager.run()
