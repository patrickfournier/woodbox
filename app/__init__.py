# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from flask import Flask, make_response, jsonify
from flask.ext.sqlalchemy import SQLAlchemy

from config import config

db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    from .api_v1 import blueprint as api_v1_blueprint
    app.register_blueprint(api_v1_blueprint, url_prefix='/api/v1')

    return app


def init_db():
    db.drop_all()
    db.create_all()
