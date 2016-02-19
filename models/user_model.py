# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import binascii

from flask import current_app

from ..db import db, DatabaseInitializer
from ..utils.pbkdf2_hmac import pbkdf2_hmac


user_roles = db.Table('wb_user_roles_association',
                      db.Column('user_id', db.Integer,
                                db.ForeignKey('wb_user_model.id'),
                                nullable=False, index=True),
                      db.Column('role_id', db.Integer,
                                db.ForeignKey('wb_role_model.id'),
                                nullable=False, index=True) )


class WBRoleModel(db.Model):
    """A user role.

    Roles are used to manage access to resources.
    """
    id = db.Column(db.Integer, db.Sequence('wb_role_model_id_seq'), primary_key=True)
    type = db.Column(db.String(50))
    rolename = db.Column(db.String(50), nullable=False, unique=True)

    __mapper_args__ = {
        'polymorphic_identity': 'wb_role_model',
        'polymorphic_on': type
    }

    anonymous_role_name = '__anonymous'
    _anonymous_role_id = None

    @classmethod
    def get_anonymous_role_id(cls):
        """Return the anonymous role id."""
        if cls._anonymous_role_id is None:
            anonymous_role = WBRoleModel.query.filter_by(rolename=cls.anonymous_role_name).first()
            cls._anonymous_role_id = anonymous_role.id
        return cls._anonymous_role_id


class WBRoleModelInitializer(DatabaseInitializer):
    """Database initializer for roles: insert the anonymous role."""
    @staticmethod
    def do_init():
        anonymous_role = WBRoleModel(rolename=WBRoleModel.anonymous_role_name)
        db.session.add(anonymous_role)
        db.session.commit()



class WBUserModel(db.Model):
    """A user of the API."""
    id = db.Column(db.Integer, db.Sequence('wb_user_model_id_seq'), primary_key=True)
    type = db.Column(db.String(50))
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    hashed_password = db.Column(db.String(64), nullable=False)

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
