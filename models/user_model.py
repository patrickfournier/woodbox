# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import binascii

from flask import current_app

from ..db import db
from ..utils.pbkdf2_hmac import pbkdf2_hmac

user_roles = db.Table('wb_user_roles_association',
                      db.Column('user_id', db.Integer, db.ForeignKey('wb_user_model.id')),
                      db.Column('role_id', db.Integer, db.ForeignKey('wb_role_model.id'))
)


class WBRoleModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('wb_role_model_id_seq'), primary_key=True)
    type = db.Column(db.String(50))
    rolename = db.Column(db.String(50), unique=True)

    __mapper_args__ = {
        'polymorphic_identity': 'wb_role_model',
        'polymorphic_on': type
    }


class WBUserModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('wb_user_model_id_seq'), primary_key=True)
    type = db.Column(db.String(50))
    username = db.Column(db.String(50), unique=True)
    hashed_password = db.Column(db.String(64))

    roles = db.relationship('WBRoleModel', secondary=user_roles)

    __mapper_args__ = {
        'polymorphic_identity': 'wb_user_model',
        'polymorphic_on': type
    }

    def __init__(self, password, **kwargs):
        hashed_password = WBUserModel.hash_password(password)
        super(WBUserModel, self).__init__(hashed_password=hashed_password, **kwargs)

    @staticmethod
    def hash_password(password):
        salt = current_app.config['PASSWORD_SALT']
        bin_hash = pbkdf2_hmac(str('sha256'), password, salt, 200000)
        return binascii.hexlify(bin_hash)
