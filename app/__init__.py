# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from flask import Flask, make_response, jsonify
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .views import populate_db

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:////tmp/martaban.db'
    #app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql://martaban:martaban@localhost/martaban'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
    app.config["SQLALCHEMY_ECHO"] = True
    db.init_app(app)

    from .api_v1 import blueprint as api_v1_blueprint
    app.register_blueprint(api_v1_blueprint, url_prefix='/api/v1')

    app.add_url_rule('/init', 'init', populate_db)
    return app

def init_db():
    db.drop_all()
    db.create_all()
