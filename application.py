from flask import Flask, render_template, request, jsonify, redirect,url_for
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Sport, Item

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

engine = create_engine('sqlite:///itemCatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog App"

# home page (SQL Read (CRUD))
@app.route('/')
@app.route('/sport/')
def showSports():
	sports = session.query(Sport).order_by(asc(Sport.sportName))
	items = session.query(Item).order_by(desc(Item.id))
	return render_template('sports.html', sports = sports, items = items)

# Make a token for oauth
@app.route('/login')
def loginPage():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
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

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(username=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showSports'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# JSON APIs to view Catalog Information
@app.route('/sport/<int:sport_id>/JSON')
def itemCatalogJSON(sport_id):
    sport = session.query(Sport).filter_by(id=sport_id).one()
    items = session.query(Item).filter_by(
        sport_id=sport_id).all()
    return jsonify(Sport=[i.serialize for i in items])


@app.route('/sport/<int:sport_id>/catalog/<int:item_id>/JSON')
def catalogItemJSON(sport_id, item_id):
    catalogItem = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=catalogItem.serialize)


@app.route('/sport/JSON')
def sportsJSON():
    sports = session.query(Sport).all()
    return jsonify(sports=[r.serialize for r in sports])

# SQL Create (CRUD)
@app.route('/sport/new', methods=['GET', 'POST'])
def addSport():
	if request.method == 'GET':
		return render_template('addsport.html')

	elif request.method == 'POST':
		newSport = Sport(
			sportName=request.form['sportName'])
		session.add(newSport)
		session.commit()
		return redirect(url_for('showSports'))

# SQL Update (CRUD)
@app.route('/sport/<int:sport_id>/edit/', methods=['GET', 'POST'])
def editSport(sport_id):
	editedSport = session.query(Sport).filter_by(id=sport_id).one()
	if request.method == 'POST':
		if request.form['sportName']:
			editedSport.sportName = request.form['sportName']
			session.add(editedSport)
			session.commit()
			return redirect(url_for('showSports'))
	else:
		return render_template('editsport.html', sport = editedSport)

# SQL Delete (CRUD)
@app.route('/sport/<int:sport_id>/delete/', methods=['GET', 'POST'])
def deleteSport(sport_id):
	deletedSport = session.query(Sport).filter_by(id=sport_id).one()
	if request.method == 'POST':
		session.delete(deletedSport)
		session.commit()
		return redirect(url_for('showSports'))
	else:
		return render_template('deletesport.html', sport = deletedSport)

# Show a sport's item list
@app.route('/sport/<int:sport_id>/')
@app.route('/sport/<int:sport_id>/catalog/')
def showCatalog(sport_id):
	sport = session.query(Sport).filter_by(id=sport_id).one()
	items = session.query(Item).filter_by(sport_id=sport_id).all()
	return render_template('catalog.html', sport = sport, items = items)

# Add catalog item to specific sport
@app.route('/sport/<int:sport_id>/new', methods=['GET', 'POST'])
def addCatalogItem(sport_id):
	sport = session.query(Sport).filter_by(id=sport_id).one()
	if request.method == 'POST':
		newCatalogItem = Item(
			name = request.form['itemName'],
			description = request.form['itemDescription'],
			sport_id = sport_id)
		session.add(newCatalogItem)
		session.commit()
		return redirect(url_for('showCatalog', sport_id = sport_id))
	else:
		return render_template('newcatalogitem.html', sport_id=sport_id)

# view individual item and description
@app.route('/sport/<int:sport_id>/catalog/<int:item_id>/')
def viewItem(sport_id, item_id):
	sport = session.query(Sport).filter_by(id=sport_id).one()
	item = session.query(Item).filter_by(id=item_id).one()
	return render_template('viewitem.html', sport_id=sport_id, item_id=item_id, item=item, sport=sport)

# edit individual item
@app.route('/sport/<int:sport_id>/catalog/<int:item_id>/edit', methods=['GET','POST'])
def editItem(sport_id, item_id):
	sport = session.query(Sport).filter_by(id=sport_id).one()
	editedItem = session.query(Item).filter_by(id=item_id).one()
	if request.method == 'POST':
		if request.form['name']:
			editedItem.name = request.form['name']
		if request.form['description']:
			editedItem.description = request.form['description']	
		session.add(editedItem)
		session.commit()
		return redirect(url_for('showCatalog', sport_id = sport_id))
	else:
		return render_template('edititem.html', sport_id = sport_id, item_id = item_id, sport=sport,  item = editedItem)


def getAllSports():
	sports = session.query(Sport).all()
	return jsonify(Sports=[i.serialize for i in sports])

def newSport(sportName):
	sportName = Sport(sportName=sportName)
	session.add(sportName)
	session.commit()
	return getAllSports()


if __name__ == '__main__':
	app.secret_key = "0R1u6gZSHgNdxmFS-ZB1fyk3" 
	app.debug = True
	app.run(host='0.0.0.0', port=5000)	