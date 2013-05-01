# -*- coding: utf-8 -*-
import os, datetime
import re
from unidecode import unidecode
import serial
import time
import glob

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

numberOfSwitches = 6

# Serial:
SerialPorts = glob.glob('/dev/tty.usb*') + glob.glob('/dev/cu.usb*')
ser = serial.Serial(SerialPorts[0], 9600, timeout=1) # create the serial object

# --------- Database Connection ---------
# MongoDB connection to MongoLab's database
connect('mydata', host=os.environ.get('MONGOLAB_URI'))
app.logger.debug("Connecting to MongoLabs")

# --------- Routes ----------

# this is our main page
@app.route("/", methods=['GET','POST'])
def index():
	currentSwitch = 1
	# if form was submitted...
	if request.method == "POST":
		# get form data - create new term
		term = models.Term()
		term.text = request.form.get('text')
		term.action = request.form.get('action')
		term.switch = request.form.get('switch')
		currentSwitch = request.form.get('switch')
		term.save() # save it

	# render the template
	templateData = {
		'filters' : models.Term.objects(),
		'numberOfSwitches' : numberOfSwitches,
		'currentSwitch' : currentSwitch
		}
	return render_template("main.html", **templateData)

# to get the json:
@app.route("/json", methods=['GET'])
def json():
	ser.flushInput() # Clear the buffer
	ser.write('a')
	inByte = ser.read(1) # Grab the next byte (timesout after 1 sec, as set above)
	try:
		inByte = int(inByte.encode('hex'), 16) #Convert the hex string into an int.
	except:
		app.logger.debug("No response from Arduino")
		inByte = 0


	terms = models.Term.objects()

	if terms:
		public_terms = []

		#prep data for json

		for t in terms:
			if (t.switch == 1 and inByte&1) or (t.switch == 2 and inByte&2) or (t.switch == 3 and inByte&4) or (t.switch == 4 and inByte&8) or (t.switch == 5 and inByte&16):
				tmpTerm = {
					'text': t.text,
					'action': t.action
					}
				public_terms.append(tmpTerm)

		data = {
			'status' : 'OK',
			'terms' : public_terms
			}

		return jsonify(data)

	else:
		error = {
			'status' : 'error',
			'msg' : 'unable to retrieve terms'
		}
		return jsonify(error)

@app.route("/click", methods=['GET'])
def click():
	ser.write('H')
	data = {
		'status' : 'OK'
		}
	return jsonify(data)

@app.route("/delete", methods=['POST'])
def delete():
	currentSwitch = request.form.get('switch');
	toDelete = request.form.get('id')
	term = models.Term.objects.get(id=toDelete)
	term.delete() # save it
	templateData = {
		'filters' : models.Term.objects(),
		'numberOfSwitches' : numberOfSwitches,
		'currentSwitch' : currentSwitch
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



	