# -*- coding: utf-8 -*-
import os, datetime
import re
from unidecode import unidecode


from flask import Flask, request, render_template, redirect, abort

# import all of mongoengine
from mongoengine import *

# import data models
import models

# for json needs
import json
from flask import jsonify

import requests

app = Flask(__name__)   # create our flask app
app.config['CSRF_ENABLED'] = False

# --------- Database Connection ---------
# MongoDB connection to MongoLab's database
connect('mydata', host=os.environ.get('MONGOLAB_URI'))
app.logger.debug("Connecting to MongoLabs")

# --------- Routes ----------

# this is our main page
@app.route("/", methods=['GET','POST'])
def index():
	# if form was submitted...
	if request.method == "POST":
		# get form data - create new term
		term = models.Term()
		term.text = request.form.get('text')
		term.action = request.form.get('action','censor')
	
		term.save() # save it

	# render the template
	templateData = {
		'terms' : models.Term.objects(),
		}
	return render_template("main.html", **templateData)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# --------- Server On ----------
# start the webserver
if __name__ == "__main__":
	app.debug = True
	
	port = int(os.environ.get('PORT', 5000)) # locally PORT 5000, Heroku will assign its own port
	app.run(host='0.0.0.0', port=port)



	