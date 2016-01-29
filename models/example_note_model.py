# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from app.db import db

class ExampleNoteModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    location = db.Column(db.String(80))
    priority = db.Column(db.Integer)
    date_created = db.Column(db.String(80))
    obsolete = db.Column(db.Boolean)

    def __repr__(self):
        return "<ExampleNote(Title='%s', Location='%s', Priority='%s')>" % (
            self.title, self.location, self.priority)
