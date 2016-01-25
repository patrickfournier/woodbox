# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from flask import Blueprint, make_response, jsonify
from flask_restful import Api

from app.record_api import make_api
from app.models.user_model import UserModel
from app.models.video_sequence_model import NodeModel, FolderNodeModel, DocumentNodeModel

from .user import UserSchema
from .video_sequence import NodeSchema, FolderNodeSchema, DocumentNodeSchema, ContentNodeSchema

blueprint = Blueprint('api_v1', __name__)
api = Api(blueprint)

@api.representation('application/vnd.api+json')
def output_jsonapi(data, code, headers=None):
    resp = make_response(jsonify(data), code)
    resp.headers.extend(headers or {})
    return resp

make_api(api, 'User', UserModel, UserSchema)

make_api(api, 'Node', NodeModel, NodeSchema)
make_api(api, 'FolderNode', FolderNodeModel, FolderNodeSchema)
make_api(api, 'DocumentNode', DocumentNodeModel, DocumentNodeSchema)
make_api(api, 'ContentNode', NodeModel, ContentNodeSchema, ro=True)
