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

# hardcoded categories for the checkboxes on the form
categories = ['web','physical computing','software','video','music','installation','assistive technology','developing nations','business','social networks']

# --------- Routes ----------

@app.route("/fsqtest")
def fsqtest():

	# Foursquare API endpoint for Venues
	fsq_url = "https://api.foursquare.com/v2/venues/search"

	# prepare the foursquare query parameters for the Venues Search request
	# simple example includes lat,long search
	# we pass in our client id and secret along with 'v', a version date of API.
	fsq_query = {
		'll' : '40.729425,-73.993707',
		'client_id' : os.environ.get('FOURSQUARE_CLIENT_ID'),
		'client_secret' : os.environ.get('FOURSQUARE_CLIENT_SECRET'),
		'v' : '20121105'
	}

	# using Requests library, make a GET request to the fsq_url
	# pass in the fsq_query dictionary as 'params', this will build the full URL with encoding variables.
	results = requests.get(fsq_url, params=fsq_query)

	# log out the url that was request
	app.logger.info("Requested url : %s" % results.url)

	# if we receive a 200 HTTP status code, great! 
	if results.status_code == 200:

		app.logger.info("received data:")
		app.logger.info(type(results.json))
		
		# get the response, venue array 
		fsq_response = results.json # .json returns a python dictonary to us.
		nearby_venues = fsq_response['response']['venues']

		app.logger.info('nearby venues')
		app.logger.info(nearby_venues)

		# Return raw json for demonstration purposes. 
		# You would likely use this data in your templates or database in a real app
		return jsonify(results.json['response'])
	
	else:

		# Foursquare API request failed somehow
		return "uhoh, something went wrong %s" % results.json

	
# this is our main page
@app.route("/", methods=['GET','POST'])
def index():

	# get Idea form from models.py
	idea_form = models.IdeaForm(request.form)
	
	# if form was submitted and it is valid...
	if request.method == "POST" and idea_form.validate():
	
		# get form data - create new idea
		idea = models.Idea()
		idea.creator = request.form.get('creator','anonymous')
		idea.title = request.form.get('title','no title')
		idea.slug = slugify(idea.title + " " + idea.creator)
		idea.idea = request.form.get('idea','')
		idea.categories = request.form.getlist('categories') # getlist will pull multiple items 'categories' into a list
		
		idea.save() # save it

		# redirect to the new idea page
		return redirect('/ideas/%s' % idea.slug)

	else:

		# for form management, checkboxes are weird (in wtforms)
		# prepare checklist items for form
		# you'll need to take the form checkboxes submitted
		# and idea_form.categories list needs to be populated.
		if request.method=="POST" and request.form.getlist('categories'):
			for c in request.form.getlist('categories'):
				idea_form.categories.append_entry(c)


		# render the template
		templateData = {
			'ideas' : models.Idea.objects(),
			'categories' : categories,
			'form' : idea_form
		}
		return render_template("main.html", **templateData)

# Display all ideas for a specific category
@app.route("/category/<cat_name>")
def by_category(cat_name):

	# try and get ideas where cat_name is inside the categories list
	try:
		ideas = models.Idea.objects(categories=cat_name)

	# not found, abort w/ 404 page
	except:
		abort(404)

	# prepare data for template
	templateData = {
		'current_category' : {
			'slug' : cat_name,
			'name' : cat_name.replace('_',' ')
		},
		'ideas' : ideas,
		'categories' : categories
	}

	# render and return template
	return render_template('category_listing.html', **templateData)


@app.route("/ideas/<idea_slug>")
def idea_display(idea_slug):

	# get idea by idea_slug
	try:
		idea = models.Idea.objects.get(slug=idea_slug)
	except:
		abort(404)

	# prepare template data
	templateData = {
		'idea' : idea
	}

	# render and return the template
	return render_template('idea_entry.html', **templateData)

@app.route("/ideas/<idea_slug>/edit", methods=['GET','POST'])
def idea_edit(idea_slug):

	
	# try and get the Idea from the database / 404 if not found
	try:
		idea = models.Idea.objects.get(slug=idea_slug)
		
		# get Idea form from models.py
		# if http post, populate with user submitted form data
		# else, populate the form with the database record
		idea_form = models.IdeaForm(request.form, obj=idea)	
	except:
		abort(404)

	# was post received and was the form valid?
	if request.method == "POST" and idea_form.validate():
	
		# get form data - update a few fields
		# note we're skipping the update of slug (incase anyone has previously bookmarked)
		idea.creator = request.form.get('creator','anonymous')
		idea.title = request.form.get('title','no title')
		idea.idea = request.form.get('idea','')
		idea.categories = request.form.getlist('categories')

		idea.save() # save changes

		return redirect('/ideas/%s/edit' % idea.slug)

	else:

		# for form management, checkboxes are weird (in wtforms)
		# prepare checklist items for form
		# you'll need to take the form checkboxes submitted
		# and idea_form.categories list needs to be populated.
		if request.method=="POST" and request.form.getlist('categories'):
			for c in request.form.getlist('categories'):
				idea_form.categories.append_entry(c)

		templateData = {
			'categories' : categories,
			'form' : idea_form,
			'idea' : idea
		}

		return render_template("idea_edit.html", **templateData)


@app.route("/ideas/<idea_id>/comment", methods=['POST'])
def idea_comment(idea_id):

	name = request.form.get('name')
	comment = request.form.get('comment')

	if name == '' or comment == '':
		# no name or comment, return to page
		return redirect(request.referrer)


	#get the idea by id
	try:
		idea = models.Idea.objects.get(id=idea_id)
	except:
		# error, return to where you came from
		return redirect(request.referrer)


	# create comment
	comment = models.Comment()
	comment.name = request.form.get('name')
	comment.comment = request.form.get('comment')
	
	# append comment to idea
	idea.comments.append(comment)

	# save it
	idea.save()

	return redirect('/ideas/%s' % idea.slug)


@app.route('/data/ideas')
def data_ideas():
	ideas = models.Idea.objects().order_by('-timestamp')

	if ideas:
		public_ideas = []

		#prep data for json
		for i in ideas:
			
			tmpIdea = {
				'creator' : i.creator,
				'title' : i.title,
				'idea' : i.idea,
				'timestamp' : str( i.timestamp )
			}

			# comments / our embedded documents

			tmpIdea['comments'] = [] # list - will hold all comment dictionaries
			
			# loop through idea comments
			for c in i.comments:
				comment_dict = {
					'name' : c.name,
					'comment' : c.comment,
					'timestamp' : str( c.timestamp )
				}

				# append comment_dict to ['comments']
				tmpIdea['comments'].append(comment_dict)

			public_ideas.append( tmpIdea )

		# prepare dictionary for JSON return
		data = {
			'status' : 'OK',
			'ideas' : public_ideas
		}

		# jsonify (imported from Flask above)
		# will convert 'data' dictionary and 
		return jsonify(data)

	else:
		error = {
			'status' : 'error',
			'msg' : 'unable to retrieve ideas'
		}
		return jsonify(error)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# slugify the title 
# via http://flask.pocoo.org/snippets/5/
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slugify(text, delim=u'-'):
	"""Generates an ASCII-only slug."""
	result = []
	for word in _punct_re.split(text.lower()):
		result.extend(unidecode(word).split())
	return unicode(delim.join(result))



# --------- Server On ----------
# start the webserver
if __name__ == "__main__":
	app.debug = True
	
	port = int(os.environ.get('PORT', 5000)) # locally PORT 5000, Heroku will assign its own port
	app.run(host='0.0.0.0', port=port)



	