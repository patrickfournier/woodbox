# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from marshmallow import ValidationError

def is_not_empty(data):
    if not data:
        raise ValidationError('This field must not be empty.')
