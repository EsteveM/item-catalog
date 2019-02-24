from flask import Flask, render_template, request, redirect, jsonify
from flask import url_for, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').
                       read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#############################################################################
#
#          Users can log into the application to authenticate and obtain
#          authorization to add, edit and delete their own items.
#
##############################################################################

# Log into the application - the server directs the user to the login page


@app.route('/login')
def showLogin():
    # Create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

#############################################################################
#
#          Connection to the application via a third party provider (Google)
#
##############################################################################

# Once the user has authenticated with the third party provider (Google), the
# server is sent the one-time-use code. If all validations described below are
# successful, the server displays a successful login message, and redirects
# the user to the application's home page.


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        flash('Login unsuccessful due to invalid state token')
        response = make_response(json.dumps(''), 401)
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
        flash('''Login unsuccessful due to failure to upgrade the authorization
                code.''')
        response = make_response(json.dumps(''), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # Verify that there is not an error in the access token information
    if result.get('error') is not None:
        flash('''Login unsuccessful due to an error in the access token
                 information.''')
        response = make_response(json.dumps(''), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        flash('''Login unsuccessful due to token's user ID not matching given
                 user ID.''')
        response = make_response(json.dumps(''), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this application
    if result['issued_to'] != CLIENT_ID:
        flash('''Login unsuccessful due to token's client ID not matching
                 application's.''')
        response = make_response(json.dumps(''), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that current user is not already connected
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        flash('Login unsuccessful due to current user already connected.')
        response = make_response(json.dumps(''), 409)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token and user in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info from third party provider (Google)
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # Store user info from third party provider (Google)
    # Username is assigned the email value because name is not always present
    # in the answer
    login_session['username'] = data['email']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # If the logged in user does not exist in our database yet, it is created
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # At this point, the log in has been successful, and the server returns a
    # welcome screen
    flash("You are now logged in as %s" % login_session['username'])
    return render_template('welcome.html', login_session=login_session)

##############################################################################
#
#       Disconnection from the application via a third party provider (Google)
#
##############################################################################

# Disconnect form the application: revoke the current user's token, and reset
# their login_session.


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user
    access_token = login_session.get('access_token')
    if access_token is None:
        flash("Current user not connected.")
        return redirect(url_for('showCategories'))
    # Revoke access token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's session
        disconnectedUsername = login_session['username']
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['picture']
        del login_session['email']
        flash('User %s has been successfully disconnected.'
              % disconnectedUsername)
    else:
        flash("Failed to revoke token for user %s" % login_session['username'])
    # Return to the root page, where the corresponding flashed messages will
    # be shown
    return redirect(url_for('showCategories'))

#############################################################################
#
#          User helper functions to create a user, get its information, and
#          get its user id.
#
##############################################################################

# Create a user from the login_session data and return its id


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

# Get a user information from its id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

# Get a user id from its email


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None

##############################################################################
#
#          JSON endpoints provided
#
##############################################################################

# JSON API to view category information


@app.route('/catalog/<string:name>/category/JSON')
def categoryJSON(name):
    try:
        category = session.query(Category).filter_by(name=name).one()
        return jsonify(Category=category.serialize)
    except BaseException:
        return jsonify(Category={})

# JSON API to view item information


@app.route('/catalog/<string:title>/item/JSON')
def itemJSON(title):
    try:
        item = session.query(Item).filter_by(title=title).one()
        return jsonify(Item=item.serialize)
    except BaseException:
        return jsonify(Item={})

# JSON API to view all categories information


@app.route('/catalog/category/JSON')
def categoriesJSON():
    try:
        categories = session.query(Category).order_by(asc(Category.id))
        return jsonify(Categories=[c.serialize for c in categories])
    except BaseException:
        return jsonify(Categories={})

# JSON API to view all items information


@app.route('/catalog/item/JSON')
def itemsJSON():
    try:
        items = session.query(Item).order_by(desc(Item.id))
        return jsonify(Items=[i.serialize for i in items])
    except BaseException:
        return jsonify(Items={})

# JSON API to view category information plus the items of the category


@app.route('/catalog/<string:name>/category/item/JSON')
def itemsCategoryJSON(name):
    try:
        category = session.query(Category).filter_by(name=name).one()
        items = session.query(Item).filter_by(
            category_id=category.id).order_by(desc(Item.id)).all()
        category = category.serialize
        itemsCategory = [i.serialize for i in items]
        category["items"] = itemsCategory
        return jsonify(Category=category)
    except BaseException:
        return jsonify(Category={})

# JSON API to view category information plus the items of the category
# for all categories in the system


@app.route('/catalog/category/item/JSON')
def allItemsCategoriesJSON():
    try:
        catalog = []
        categories = session.query(Category).order_by(asc(Category.id))
        for category in categories:
            items = session.query(Item).filter_by(
                category_id=category.id).order_by(desc(Item.id)).all()
            category = category.serialize
            itemsCategory = [i.serialize for i in items]
            category["items"] = itemsCategory
            catalog.append(category)
        return jsonify(Catalog=catalog)
    except BaseException:
        return jsonify(Catalog={})

##############################################################################
#
#          Homepage: All categories and latest items
#                    After logon, users have the option to add an item from
#                    the homepage
#
##############################################################################

# Show all categories and latest items


@app.route('/')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.id))
    # Only the latest items are shown. In this case, a limit of the latest 9
    # items has been chosen.
    items = session.query(Item).order_by(desc(Item.id)).limit(9)
    if 'username' not in login_session:
        return render_template('publiccategories.html', categories=categories,
                               items=items)
    else:
        return render_template('categories.html', categories=categories,
                               items=items)

##############################################################################
#
#          Selecting a category shows all its items
#
##############################################################################

# Show a category items


@app.route('/catalog/<string:name>/items/')
def showItems(name):
    try:
        category = session.query(Category).filter_by(name=name).one()
        items = session.query(Item).filter_by(
            category_id=category.id).order_by(desc(Item.id)).all()
        categories = session.query(Category).order_by(asc(Category.id))
        itemsLength = len(items)
    except BaseException:
        flash('The query has been unsuccessful')
        return redirect(url_for('showCategories'))
    if 'username' not in login_session:
        return render_template('publicitems.html', categories=categories,
                               items=items, category=category,
                               itemsLength=itemsLength)
    else:
        return render_template('items.html', categories=categories,
                               items=items, category=category,
                               itemsLength=itemsLength)

##############################################################################
#
#          Selecting an item shows its information
#          After logon, users have the option to edit/delete an item
#
##############################################################################

# Show an item's information


@app.route('/catalog/<string:name>/<string:title>/')
def showItem(name, title):
    try:
        item = session.query(Item).filter_by(title=title).one()
    except BaseException:
        flash('The query has been unsuccessful')
        return redirect(url_for('showCategories'))
    if 'username' not in login_session:
        return render_template('publicitem.html', item=item)
    else:
        return render_template('item.html', item=item)

##############################################################################
#
#          After logon, users can add new items. In this route, their category
#          is chosen from a select list at the page where the item is defined.
#
##############################################################################

# Create a new item


@app.route('/catalog/add/', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        flash("User not logged in. Please, log in to create new items")
        return redirect(url_for('showCategories'))
    if request.method == 'POST':
        try:
            category = session.query(Category).filter_by(
                                    name=request.form['category']).one()
            item = session.query(Item).filter_by(
                title=request.form['title']).first()
            # It is not going to be allowed to add two items which have the
            # the same title
            if item is None:
                newItem = Item(title=request.form['title'],
                               description=request.form['description'],
                               category_id=category.id,
                               user_id=login_session['user_id'])
                session.add(newItem)
                session.commit()
                flash('New item "%s" successfully created'
                      % (request.form['title']))
                return redirect(url_for('showCategories'))
            else:
                flash("Item %s already exists"
                      % (request.form['title']))
                return redirect(url_for('showCategories'))
        except BaseException:
            flash('New item creation was unsuccessful')
            return redirect(url_for('showCategories'))
    else:
        categories = session.query(Category).order_by(asc(Category.id))
        return render_template('newItem.html', categories=categories)

##############################################################################
#
#          After logon, users can add new items. In this route, their category
#          is fixed at the page where the item is defined. This is because
#          their category is already known in the homepage.
#
##############################################################################

# Create a new category item


@app.route('/catalog/<string:name>/add/', methods=['GET', 'POST'])
def newCategoryItem(name):
    if 'username' not in login_session:
        flash('''User not logged in. Please, log in to create new category
                 items''')
        return redirect(url_for('showCategories'))
    if request.method == 'POST':
        try:
            category = session.query(Category).filter_by(name=name).one()
            item = session.query(Item).filter_by(
                title=request.form['title']).first()
            # It is not going to be allowed to add two items which have the
            # the same title
            if item is None:
                newItem = Item(title=request.form['title'],
                               description=request.form['description'],
                               category_id=category.id,
                               user_id=login_session['user_id'])
                session.add(newItem)
                session.commit()
                flash('New "%s" item "%s" successfully created'
                      % (name, request.form['title']))
                return redirect(url_for('showCategories'))
            else:
                flash("Item %s already exists"
                      % (request.form['title']))
                return redirect(url_for('showCategories'))
        except BaseException:
            flash('New item creation was unsuccessful')
            return redirect(url_for('showCategories'))
    else:
        category = session.query(Category).filter_by(name=name).first()
        if category is None:
            flash('''Creation of new item unsuccessful. Category "%s"
                  does not exist''' % (name))
            return redirect(url_for('showCategories'))
        else:
            return render_template('newCategoryItem.html', category_name=name)

##############################################################################
#
#          After logon, users can edit item information. However, they can
#          only edit the items that they have created.
#
##############################################################################

# Edit an item


@app.route('/catalog/<string:title>/edit', methods=['GET', 'POST'])
def editItem(title):
    if 'username' not in login_session:
        flash('User not logged in. Please, log in to edit items')
        return redirect(url_for('showCategories'))
    toEditItem = session.query(Item).filter_by(title=title).first()
    if toEditItem is None:
        flash('''Edition of new item unsuccessful. Item "%s"
                  does not exist''' % (title))
        return redirect(url_for('showCategories'))
    if login_session['user_id'] != toEditItem.user_id:
        flash('''You are not authorized to edit the "%s" item. You can only
              edit items that you have created''' % (title))
        return redirect(url_for('showCategories'))
    if request.method == 'POST':
        if request.form['description']:
            toEditItem.description = request.form['description']
        if request.form['category']:
            category = session.query(Category).filter_by(
                name=request.form['category']).one()
            toEditItem.category_id = category.id
        session.add(toEditItem)
        session.commit()
        flash('Item %s has been successfully edited'
              % (toEditItem.title))
        return redirect(url_for('showCategories'))
    else:
        categories = session.query(Category).order_by(asc(Category.id))
        return render_template('editItem.html', categories=categories,
                               item=toEditItem)

##############################################################################
#
#          After logon, users can delete items. However, they can
#          only delete those items that they have created.
#
##############################################################################

# Delete an item


@app.route('/catalog/<string:title>/delete', methods=['GET', 'POST'])
def deleteItem(title):
    if 'username' not in login_session:
        flash('User not logged in. Please, log in to delete items')
        return redirect(url_for('showCategories'))
    item = session.query(Item).filter_by(title=title).first()
    if item is None:
        flash('''Deletion unsuccessful. Item "%s"
                  does not exist''' % (title))
        return redirect(url_for('showCategories'))
    if login_session['user_id'] != item.user_id:
        flash('''You are not authorized to delete the "%s" item. You can only
              delete items that you have created''' % (title))
        return redirect(url_for('showCategories'))
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash('Item %s has been successfully deleted' % (item.title))
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteItem.html', item=item)

##############################################################################
#
#          Main program execution
#
##############################################################################


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
