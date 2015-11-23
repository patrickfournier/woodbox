# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from . import db
from .video_sequence_model import VideoSequenceModel

def populate_db():
    db.drop_all()
    db.create_all()
    data = {'title': 'Yo', 'location': 'Montreal', 'sequence_number': 1, 'date_created':  '2015-04-23T13:38', 'processed': False}
    vs = VideoSequenceModel(**data)
    db.session.add(vs)
    data = {'title': 'Yo', 'location': 'Laval', 'sequence_number': 13, 'date_created': '2015-04-23T14:38', 'processed': True}
    vs = VideoSequenceModel(**data)
    db.session.add(vs)
    db.session.commit()
    return 'DB Initialization Done'
