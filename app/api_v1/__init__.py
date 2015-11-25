# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from flask import Blueprint, make_response, jsonify
from flask_restful import Api

from .example_note import ExampleNoteAPI, ExampleNoteListAPI

blueprint = Blueprint('api_v1', __name__)
api = Api(blueprint)

@api.representation('application/vnd.api+json')
def output_jsonapi(data, code, headers=None):
    resp = make_response(jsonify(data), code)
    resp.headers.extend(headers or {})
    return resp

api.add_resource(ExampleNoteListAPI, '/example-notes')
api.add_resource(ExampleNoteAPI, '/example-notes/<item_id>')
