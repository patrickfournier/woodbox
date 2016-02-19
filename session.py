# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from flask import jsonify, request

from .db import db
from .models.session_model import WBSessionModel
from .models.user_model import WBUserModel


def authenticate():
    """View function to authenticate user.

    If authentication is successful, a new session is created and
    returned as a response.

    """
    try:
        name = request.form['username']
        password = request.form['password']
    except KeyError:
        return jsonify(err=2, message="Missing parameter.")

    user = WBUserModel.query.filter_by(username=name).first()
    hashed_password = WBUserModel.hash_password(password)
    if user and user.hashed_password == hashed_password:
        session = WBSessionModel(user_id=user.id)
        db.session.add(session)
        db.session.commit()
        return jsonify(username=name, err=0,
                       session_id=session.session_id,
                       session_secret=session.secret)
    else:
        return jsonify(err=1, message="Invalid credentials.")


def validate_session():
    """View function to check if session id refers to a valid session."""
    session_id = request.form['session_id']
    session = WBSessionModel.query.filter_by(session_id=session_id).first()
    if session and session.touch():
        return jsonify(err=0)

    return jsonify(err=3, message="Invalid session.")


def invalidate_session():
    """View function to delete the session referenced in the request."""
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
    """Helper function to register URL routes for session management.

    Register POST URL routes for the three session management
    functions :func:`authenticate`, :func:`validate_session` and
    :func:`invalidate_session`.

    Arguments:
    app -- a Flask app

    Keyword arguments:
    authenticate_url -- URL for the :func:`authenticate` function, default to ``/authenticate``
    validate_url -- URL for the :func:`validate_session` function, default to ``/validate-session``
    invalidate_url -- URL for the :func:`invalidate_session` function, default to ``/invalidate-session``

    """
    app.add_url_rule(authenticate_url, 'authenticate', authenticate, methods=['POST'])
    app.add_url_rule(validate_url, 'validate_session', validate_session, methods=['POST'])
    app.add_url_rule(invalidate_url, 'invalidate_session', invalidate_session, methods=['POST'])
