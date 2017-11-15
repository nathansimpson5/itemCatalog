from flask import Flask, render_template, request, jsonify, redirect,url_for
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Sport, Item


engine = create_engine('sqlite:///itemCatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

@app.route('/')
@app.route('/sport/')
def showSports():
	sports = session.query(Sport).order_by(asc(Sport.sportName))
	items = session.query(Item).order_by(desc(Item.id))
	all = session.query(Sport, )
	return render_template('sports.html', sports = sports, items = items)

@app.route('/login', methods=['GET', 'POST'])
def loginPage():
	return render_template('login.html')

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


def getAllSports():
	sports = session.query(Sport).all()
	return jsonify(Sports=[i.serialize for i in sports])

def newSport(sportName):
	sportName = Sport(sportName=sportName)
	session.add(sportName)
	session.commit()
	return getAllSports()


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)	