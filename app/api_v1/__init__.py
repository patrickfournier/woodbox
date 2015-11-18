# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from flask import Blueprint, make_response, jsonify
from flask_restful import Api

from .video_sequence import VideoSequence, VideoSequenceList

blueprint = Blueprint('api_v1', __name__)
api = Api(blueprint)

@api.representation('application/vnd.api+json')
def output_jsonapi(data, code, headers=None):
    resp = make_response(jsonify(data), code)
    resp.headers.extend(headers or {})
    return resp

api.add_resource(VideoSequenceList, '/video-sequences')
api.add_resource(VideoSequence, '/video-sequence/<item_id>')
