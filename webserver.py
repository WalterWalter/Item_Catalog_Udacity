#! /usr/bin/env python3
from flask import Flask, render_template, url_for, \
     request, redirect, jsonify, flash, session
from sqlalchemy import create_engine, desc, update
from sqlalchemy.orm import sessionmaker
from setup_database import Base, User, Category, Item
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from functools import wraps
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
    'web']['client_id']

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
db_session = DBSession()


# Check if the user exists in the database, if not create new user
def checkCreateNewUser(email):
    if db_session.query(User).filter(User.email == email).count() == 0:
        new_user = User(email=email)
        db_session.add(new_user)
        db_session.commit()


# Get userID from email
def getUserId(email):
    temp = db_session.query(User.id).filter(User.email == email).one()
    return temp[0]


# Create anti-forgery state token
@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    session['state'] = state
    return render_template('login.html', STATE=state)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/login')
    return decorated_function


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if the user is already logged in
    stored_access_token = session.get('access_token')
    stored_gplus_id = session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    session['access_token'] = credentials.access_token
    session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    session['username'] = data['name']
    session['email'] = data['email']

    # Check if user exists in the database, if not create new user.
    checkCreateNewUser(session['email'])

    output = ''
    output += '<h1>Welcome, '
    output += session['username']
    output += '!</h1>'
    flash("you are now logged in as %s" % session['username'])
    print "done!"
    return output


# For disconnect from google plus
@app.route('/gdisconnect')
@login_required
def gdisconnect():
    access_token = session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del session['access_token']
        del session['gplus_id']
        del session['username']
        del session['email']
        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Main page
@app.route('/')
def index():
    # Authentication check
    if 'username' in session:
        isLogin = True
    else:
        isLogin = False

    categories = db_session.query(Category.name).order_by(Category.id).all()
    lastest_items = db_session.query(Item.name, Category.name, Item.id).filter(
        Item.category_id == Category.id).order_by(desc(Item.time_created)
                                                  ).limit(10).all()
    return render_template('index.html', categories=categories,
                           lastest_items=lastest_items, isLogin=isLogin)


@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    categories = db_session.query(Category.name, Category.id).order_by(
        Category.id).all()
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category_id=request.form['category_id'],
                       user_id=getUserId(session['email']))
        db_session.add(newItem)
        db_session.commit()
        return redirect('/')
    else:
        return render_template('add_item.html', categories=categories)


@app.route('/catalog/<category_name>/items')
def category(category_name):
    # Authentication check
    if 'username' in session:
        isLogin = True
    else:
        isLogin = False

    categories = db_session.query(Category.name).order_by(
        Category.id).all()
    Category_id = db_session.query(Category.id).filter(
        Category.name == category_name).one()
    items = db_session.query(Item.name, Item.id).filter(
        Item.category_id == Category_id[0]).order_by(Item.time_created).all()
    return render_template('category.html', categories=categories,
                           category_name=category_name, items=items,
                           isLogin=isLogin)


@app.route('/catalog/<category_name>/<item_name>/<item_id>')
def item(category_name, item_name, item_id):
    # Authentication check
    if 'username' in session:
        isLogin = True
    else:
        isLogin = False

    # Authorization check
    if isLogin is False:
        isAllow = False
    else:
        user_id = db_session.query(Item.user_id).filter(
            Item.id == item_id).one()
        user_email = db_session.query(User.email).filter(
            User.id == user_id[0]).one()
        if user_email[0] == session['email']:
            isAllow = True
        else:
            isAllow = False

    description = db_session.query(Item.description).filter(
        Item.id == item_id).one()
    return render_template('item.html', item_name=item_name,
                           description=description[0], isLogin=isLogin,
                           isAllow=isAllow, item_id=item_id,
                           category_name=category_name)


@app.route('/catalog/<category_name>/<item_name>/<item_id>/edit',
           methods=['GET', 'POST'])
@login_required
def edit_item(category_name, item_name, item_id):
    # Authorization required
    user_id = db_session.query(Item.user_id).filter(
        Item.id == item_id).one()
    user_email = db_session.query(User.email).filter(
        User.id == user_id[0]).one()
    if user_email[0] != session['email']:
        return "You are not allowed to edit this item."

    categories = db_session.query(Category.name, Category.id).order_by(
        Category.id).all()
    description = db_session.query(Item.description).filter(
        Item.id == item_id).one()
    category_id = db_session.query(Category.id).filter(
        Category.name == category_name).one()
    if request.method == 'POST':
        db_session.query(Item).filter(Item.id == item_id).update({
            Item.name: request.form['name'],
            Item.description: request.form['description'],
            Item.category_id: request.form['category_id']})
        db_session.commit()
        return redirect('/')
    else:
        return render_template('edit_item.html',
                               categories=categories, item_name=item_name,
                               description=description[0], item_id=item_id,
                               category_id=category_id[0])


@app.route('/catalog/<category_name>/<item_name>/<item_id>/delete',
           methods=['GET', 'POST'])
@login_required
def delete_item(category_name, item_name, item_id):
    # Authorization required
    user_id = db_session.query(Item.user_id).filter(
        Item.id == item_id).one()
    user_email = db_session.query(User.email).filter(
        User.id == user_id[0]).one()
    if user_email[0] != session['email']:
        return "You are not allowed to edit this item."
    item1 = db_session.query(Item).filter(Item.id == item_id).one()
    db_session.delete(item1)
    db_session.commit()
    return redirect('/')


# JSON endpoints for items
@app.route('/catalog/<category_name>/<item_name>/<item_id>/JSON')
def item_api(category_name, item_name, item_id):
    item = db_session.query(Item).filter(Item.id == item_id).one()
    return jsonify(item.serialize)


if __name__ == "__main__":
    app.secret_key = "not_very_secretive"
    app.run(host='0.0.0.0', port=5001)
