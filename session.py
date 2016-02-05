# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from flask import jsonify, request

from .db import db
from .models.session_model import WBSessionModel
from .models.user_model import WBUserModel


def authenticate():
    try:
        name = request.form['username']
        user = WBUserModel.query.filter_by(username=name).first()
        if user:
            password = request.form['password']
            hashed_password = WBUserModel.hash_password(password)
            if user.hashed_password == hashed_password:
                session = WBSessionModel(user_id=user.id)
                db.session.add(session)
                db.session.commit()
                response = jsonify(username=name, err=0,
                                   session_id=session.session_id,
                                   session_secret=session.secret)
            else:
                response = jsonify(err=1, message="Invalid credentials.")
        else:
            response = jsonify(err=1, message="Invalid credentials.")
    except KeyError:
        response = jsonify(err=2, message="Missing parameter.")

    return response


def validate_session():
    session_id = request.form['session_id']
    session = WBSessionModel.query.filter_by(session_id=session_id).first()
    if session and session.touch():
        return jsonify(err=0)

    return jsonify(err=3, message="Invalid session.")


def invalidate_session():
    session_id = request.form['session_id']
    session = WBSessionModel.query.filter_by(session_id=session_id).first()
    if session:
        count = db.session.delete(session)
        db.session.commit()
        if count == 0:
            return jsonify(err=4, message="Session could not be deleted.")

    return jsonify(err=0)


def add_session_management_urls(app, authenticate_url='/authenticate',
                                validate_url='/validate-session',
                                invalidate_url='/invalidate-session'):
    app.add_url_rule(authenticate_url, 'authenticate', authenticate, methods=['POST'])
    app.add_url_rule(validate_url, 'validate_session', validate_session, methods=['POST'])
    app.add_url_rule(invalidate_url, 'invalidate_session', invalidate_session, methods=['POST'])
