#! /usr/bin/env python3
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
        __tablename__ = 'user'
        id = Column(Integer, primary_key=True)
        email = Column(String(250), nullable=False)


class Category(Base):
        __tablename__ = 'category'
        id = Column(Integer, primary_key=True)
        name = Column(String(100), nullable=False)


class Item(Base):
        __tablename__ = 'item'
        id = Column(Integer, primary_key=True)
        name = Column(String(250), nullable=False)
        description = Column(String(500))
        category_id = Column(Integer, ForeignKey('category.id'))
        category = relationship("Category", cascade="all")
        user_id = Column(Integer, ForeignKey('user.id'))
        user = relationship("User", cascade="all")
        time_created = Column(DateTime(timezone=True),
                              server_default=func.now())
        """
        Return object data in serialized format
        """
        @property
        def serialize(self):
                return {
                        'id': self.id,
                        'name': self.name,
                        'description': self.description,
                        'category_id': self.category_id,
                        'user_id': self.user_id
                        }


engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
