import os, datetime
from flask import Flask, request, render_template

app = Flask(__name__)   # create our flask app



# this is our main page
@app.route("/")
def index():
	# render the template, pass in the animals dictionary refer to it as 'animals'
	return render_template("main.html")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# start the webserver
if __name__ == "__main__":
	app.debug = True
	
	port = int(os.environ.get('PORT', 5000)) # locally PORT 5000, Heroku will assign its own port
	app.run(host='0.0.0.0', port=port)



	