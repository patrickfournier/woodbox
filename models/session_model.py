# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import binascii
import hashlib
import os

from datetime import datetime, timedelta

from sqlalchemy.exc import ArgumentError

from ..db import db
from .user_model import WBUserModel

# Should be renamed Credentials
class WBSessionModel(db.Model):
    session_id_byte_length = 24
    secret_byte_length = 32

    session_max_idle_time = 60*60

    id = db.Column(db.Integer, db.Sequence('wb_session_model_id_seq'), primary_key=True)
    type = db.Column(db.String(50))
    session_id = db.Column(db.String(2*session_id_byte_length), unique=True)
    secret = db.Column(db.String(2*secret_byte_length))
    user_id = db.Column(db.Integer, db.ForeignKey('wb_user_model.id'), nullable=False)
    created = db.Column(db.DateTime)
    accessed = db.Column(db.DateTime)

    __mapper_args__ = {
        'polymorphic_identity': 'wb_session_model',
        'polymorphic_on': type
    }

    def __init__(self, user_id):
        if WBUserModel.query.filter_by(id=user_id).count() > 0:
            self.session_id = binascii.hexlify(os.urandom(self.session_id_byte_length))
            self.secret = binascii.hexlify(os.urandom(self.secret_byte_length))
            self.user_id = user_id
            self.created = datetime.utcnow()
            self.accessed = self.created
        else:
            raise ArgumentError('Unknown user id')

    def touch(self):
        if self.accessed + timedelta(seconds=self.session_max_idle_time) < datetime.utcnow():
            db.session.delete(self)
            db.session.commit()
            return False
        else:
            self.accessed = datetime.utcnow()
            db.session.commit()
            return True
