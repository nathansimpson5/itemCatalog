from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Sport


engine = create_engine('sqlite:///itemCatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

@app.route('/')
def hello_world():
	sports = session.query(Sport).all()
	return render_template('index.html', sports = sports)

@app.route('/login', methods=['GET', 'POST'])
def loginPage():
	return render_template('login.html')

# SQL Create (CRUD)
@app.route('/addsport', methods=['GET', 'POST'])
def addSport():
	if request.method == 'GET':
		return render_template('addsport.html')

	elif request.method == 'POST':
		sportName = request.form['sportName']
		return newSport(sportName)


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