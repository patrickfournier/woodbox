# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

class AccessControlElementModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('access_control_element_model_id_seq'), primary_key=True)
    resource_type = db.Column(db.String(100))
    resource_id = db.Column(db.Integer)
    role = db.Column(db.String(100))
    permission = db.Column(db.String(100))
