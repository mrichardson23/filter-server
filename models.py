# -*- coding: utf-8 -*-
from mongoengine import *

from flask.ext.mongoengine.wtf import model_form
from datetime import datetime

import logging

# our demo model from week 5 in class
class Term(Document):
	text = StringField()
	action = StringField()

