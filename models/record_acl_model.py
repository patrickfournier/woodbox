# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from ..db import db


class RecordACLModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('record_acl_model_id_seq'), primary_key=True)
    record_type = db.Column(db.String(100))
    record_id = db.Column(db.Integer)
    user_role = db.Column(db.String(50))
    permission = db.Column(db.String(50))
