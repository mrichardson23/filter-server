# Databases

## MongoDB


## Configure Heroku app


Add MongoLabs starter database to your app. [https://addons.heroku.com/mongolab](https://addons.heroku.com/mongolab)

	heroku addons:add mongolab:starter

Create your local environment variable file, **.env**

	heroku config --shell > .env


## MongoDB library - Mongoengine

[Mongoengine](http://mongoengine.org/)

Adding Mongoengine to requirements.txt

	Mongoengine==0.7.5

