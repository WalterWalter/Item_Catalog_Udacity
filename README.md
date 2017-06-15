### Item Catalog App
This is the 4th project of Udacity's Full-Stack Web Developer Nanodegree.

### About
The application provides a list of items within a variety of categories, as well as provide a third party (Google+) authentication and authorization service.

API Endpoints:
"http://0.0.0.0:5001/catalog/<category_name>/<item_name>/<item_id>/JSON" => Information for an arbitrary item in the catalog.

CRUD of database:
The website include the functions create, read , update and delete a record.
They are implemented through SQLAlchemy.

Authentication & Authorization:
It provide a third party (Google+) authentication and authorization service.
User can use create, update, delete functions only after logged-in through Google+ account.


### Technologies been used
Python3, Flask, SQLAlchemy, Google+ Authentication, Bootstrap for CSS

### How to run it
1. Install Vagrant and VirtualBox
2. Navigate to 'project4' folder:
`cd /project4`
3. Launch the Vagrant VM:
`vagrant up` and `vagrant ssh`
4. Navigate to the project directory:
`cd /vagrant`
5. Set up the database:
`python setup_database.py`
6. Populate the database:
`python catalog_populator.py`
7. Run the app:
`python webserver.py`
8. Go to: "http://0.0.0.0:5001/"


