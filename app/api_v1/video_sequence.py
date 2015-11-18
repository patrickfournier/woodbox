from flask_restful import Resource, abort

from marshmallow_jsonapi import fields

from app.jsonapi_schema import JSONAPISchema
from app.video_sequence_model import VideoSequenceModel

class VideoSequenceSchema(JSONAPISchema):
    title = fields.Str()
    location = fields.Str()
    sequence_number = fields.Str()
    date_recorded = fields.Str(attribute='date_created')
    upper_name = fields.Function(lambda obj: obj.title.upper())

class VideoSequenceList(Resource):
    def get(self):
        items = VideoSequenceModel.query.all()
        return VideoSequenceSchema().dump(items, many=True).data

class VideoSequence(Resource):
    def get(self, item_id):
        item = VideoSequenceModel.query.get(item_id)
        if item is None:
            abort(404, message="Video sequence {} doesn't exist".format(item_id))
        else:
            return VideoSequenceSchema().dump(item).data
