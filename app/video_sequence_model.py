# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from . import db

class VideoSequenceModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    location = db.Column(db.String(80))
    sequence_number = db.Column(db.String(80))
    date_created = db.Column(db.String(80))

    def __init__(self, title, location, sequence_number, date_created):
        self.title = title
        self.location = location
        self.sequence_number = sequence_number
        self.date_created = date_created
