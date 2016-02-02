# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import binascii

from flask import current_app

from ..db import db
from ..utils.pbkdf2_hmac import pbkdf2_hmac

user_roles = db.Table('user_roles',
                      db.Column('user_id', db.Integer, db.ForeignKey('user_model.id')),
                      db.Column('role_id', db.Integer, db.ForeignKey('role_model.id'))
)


class RoleModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('role_model_id_seq'), primary_key=True)
    rolename = db.Column(db.String(50), unique=True)


class UserModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('user_model_id_seq'), primary_key=True)
    username = db.Column(db.String(50), unique=True)
    hashed_password = db.Column(db.String(64))
    name = db.Column(db.String(100))

    roles = db.relationship('RoleModel', secondary=user_roles)

    def __init__(self, password, **kwargs):
        hashed_password = UserModel.hash_password(password)
        super(UserModel, self).__init__(hashed_password=hashed_password, **kwargs)

    @staticmethod
    def hash_password(password):
        salt = current_app.config['PASSWORD_SALT']
        bin_hash = pbkdf2_hmac(str('sha256'), password, salt, 200000)
        return binascii.hexlify(bin_hash)
