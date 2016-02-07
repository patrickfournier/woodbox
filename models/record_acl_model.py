# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals


from ..db import db
from .user_model import WBUserModel

class RecordACLModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('record_acl_model_id_seq'), primary_key=True)
    record_type = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    user_role_id = db.Column(db.Integer, db.ForeignKey('wb_user_model.id'), nullable=False)
    permission = db.Column(db.Enum('read', 'update', 'delete'), nullable=False)

    __table_args__ = (db.UniqueConstraint('record_type', 'record_id',
                                          'user_role_id',
                                          'permission',
                                          name='_unique_acl'),)


def make_record_acl(record_types, record_ids, user_role_ids, permissions):
    """Helper function to build a list of RecordACLModels."""
    acl = []
    for r in record_types:
        for i in record_ids:
            for u in user_role_ids:
                for p in permissions:
                    acl.append(RecordACLModel(record_type=r,
                                              record_id=i,
                                              user_role_id=u,
                                              permission=p))
    return acl
