#! /usr/bin/env python3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setup_database import Base, User, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Add users
new_user = User(email='chenlijian.csu@gmail.com')
session.add(new_user)
session.commit()

new_user = User(email='chenlijian1990@gmail.com')
session.add(new_user)
session.commit()

# Add categories
Categories = ['Soccer', 'Basketball', 'Baseball', 'Frisbee', 'Snowboarding',
              'Rock Climbing', 'Football', 'Skating', 'Hockey']

for i in range(len(Categories)):
        new_category = Category(name=Categories[i])
        session.add(new_category)
        session.commit()

# Add items
new_item = Item(name='Stick', description='''An ice hockey stick is
a piece of equipment used in ice hockey to shoot, pass, and
carry the puck across the ice.''', category_id=9, user_id=1)
session.add(new_item)
session.commit()

new_item = Item(name='Goggles', description='''Goggles or safety
        glasses are forms of protective eyewear that usually enclose
        or protect the area surrounding the eye in order to prevent
        particulates, water or chemicals from striking the eyes.''',
                category_id=5, user_id=1)
session.add(new_item)
session.commit()

new_item = Item(name='Snowboard', description='''Snowboards are boards
        that are usually the width of one's foot longways, with the
        ability to glide on snow.''', category_id=5, user_id=2)
session.add(new_item)
session.commit()
