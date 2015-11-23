# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from . import db

class VideoSequenceModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    location = db.Column(db.String(80))
    sequence_number = db.Column(db.Integer)
    date_created = db.Column(db.String(80))
    processed = db.Column(db.Boolean)

    def __repr__(self):
        return "<VideoSequenceModel(title='%s', Location='%s', Sequence number='%s')>" % (
            self.title, self.location, self.sequence_number)
