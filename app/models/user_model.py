# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import binascii

from app.db import db
from app.pbkdf2_hmac import pbkdf2_hmac


class UserModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('user_model_id_seq'), primary_key=True)
    username = db.Column(db.String(50), unique=True)
    hashed_password = db.Column(db.String(64))
    name = db.Column(db.String(100))

    def __init__(self, password, **kwargs):
        hashed_password = UserModel.hash_password(password)
        super(UserModel, self).__init__(hashed_password=hashed_password, **kwargs)

    @staticmethod
    def hash_password(password):
        salt = 'salt'
        bin_hash = pbkdf2_hmac(str('sha256'), password, salt, 200000)
        return binascii.hexlify(bin_hash)
