from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


# Create an initial user, User1
User1 = User(name="John Smith", email="User1@myapp.com",
             picture='''https://images.pexels.com/photos/364100/
             pexels-photo-364100.jpeg?cs=srgb&dl=background-backlit-beach-364100.
             jpg&fm=jpg''')
session.add(User1)
session.commit()

# Create nine initial categories
category1 = Category(name="Soccer")
session.add(category1)

category2 = Category(name="Basketball")
session.add(category2)

category3 = Category(name="Baseball")
session.add(category3)

category4 = Category(name="Frisbee")
session.add(category4)

category5 = Category(name="Snowboarding")
session.add(category5)

category6 = Category(name="Rock Climbing")
session.add(category6)

category7 = Category(name="Foosball")
session.add(category7)

category8 = Category(name="Skating")
session.add(category8)

category9 = Category(name="Hockey")
session.add(category9)

session.commit()

# Create nine initial items
Item1 = Item(user=User1, title="Stick", description="The long piece of wood",
             category=category9)
session.add(Item1)

Item2 = Item(user=User1, title="Goggles",
             description="Ski googles to take care of your eyes",
             category=category5)
session.add(Item2)

Item3 = Item(user=User1, title="Snowboard", description='Best for any ' +
             'terrain and conditions. All-mountain snowboards perform ' +
             'anywhere on a mountain - groomed runs, backcountry, even ' +
             'park and pipe. They may be directional (meaning downhill ' +
             'only) or twin-tip (for riding switch, meaning either ' +
             'direction). Most boarders ride all-mountain boards. Because' +
             ' of their versatility, all-mountain boards are good for' +
             ' beginners who are still learning what terrain they' +
             ' like.', category=category5)
session.add(Item3)

Item4 = Item(user=User1, title="Two shinguards", description='Best ' +
             'protection for your legs. Two top quality shinguards.',
             category=category1)
session.add(Item4)

Item5 = Item(user=User1, title="Shinguards", description='Shinguards are ' +
             'well-known to save your legs from injuries while playing ' +
             'soccer.', category=category1)
session.add(Item5)

Item6 = Item(user=User1, title="Frisbee", description='Have great fun ' +
             'throwing frisbees amongst your friends at the beach, or ' +
             'wherever else.', category=category4)
session.add(Item6)

Item7 = Item(user=User1, title="Bat", description='The best ones to hit the ' +
             'ball in your baseball games.', category=category3)
session.add(Item7)

Item8 = Item(user=User1, title="Jersey", description='Perfect shirts to ' +
             'equip your soccer team.', category=category1)
session.add(Item8)

Item9 = Item(user=User1, title="Soccer Cleats", description='These cleats ' +
             'will prevent you from sliding on the sports field.',
             category=category1)
session.add(Item9)

session.commit()

print "Categories and items added!"
