# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from . import db
from .video_sequence_model import VideoSequenceModel

def populate_db():
    db.drop_all()
    db.create_all()
    vs = VideoSequenceModel('Yo', 'Montreal', '1', '2015-04-23T13:38')
    db.session.add(vs)
    vs = VideoSequenceModel('Yo', 'Laval', '13', '2015-04-23T14:38')
    db.session.add(vs)
    db.session.commit()
    return 'DB Initialization Done'
