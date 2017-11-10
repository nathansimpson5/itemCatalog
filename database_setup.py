from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()


class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	username = Column(String(250), nullable = False)
	email = Column(String(250), nullable = False)

	@property
	def serialize(self):
		return {
			'id': self.id,
			'username': self.username,
			'email': self.email
		}

class Sport(Base):
	__tablename__ = 'sport'

	id = Column(Integer, primary_key=True)
	sportName = Column(String)

	@property
	def serialize(self):
		return {
			'sportName': self.sportName
		}


engine = create_engine('sqlite:///itemCatalog.db')

Base.metadata.create_all(engine)