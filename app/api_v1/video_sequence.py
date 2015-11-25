# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from marshmallow_jsonapi import fields

from app.jsonapi_schema import JSONAPISchema
from app.record_api import RecordAPI, RecordListAPI
from app.schema_validator import is_not_empty
from app.models.video_sequence_model import VideoSequenceModel


class VideoSequenceSchema(JSONAPISchema):
    title = fields.Str(required=True, validate=is_not_empty)
    location = fields.Str()
    sequence_number = fields.Int()
    date_recorded = fields.Str(attribute='date_created')
    processed = fields.Bool()
    upper_name = fields.Function(lambda obj: obj.title.upper())

class VideoSequenceAPI(RecordAPI):
    model_class = VideoSequenceModel
    schema_class = VideoSequenceSchema

class VideoSequenceListAPI(RecordListAPI):
    model_class = VideoSequenceModel
    schema_class = VideoSequenceSchema
