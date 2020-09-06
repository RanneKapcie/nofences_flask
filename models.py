from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from geoalchemy2 import Geometry
import shapely
from flask_login import UserMixin
from sqlalchemy import *
from sqlalchemy.orm import *
from sessions import db_session, engine, base, metadata

"""engine = create_engine('postgresql://postgres:postgres@localhost:5432/nofences', echo=True)
Session = sessionmaker(bind=engine)
#session = Session()"""

"""metadata = MetaData(engine)
base = declarative_base(metadata=metadata)"""


class User(UserMixin, base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    password = Column(Unicode, nullable=False)
    last_login = Column(DateTime, default=datetime.now())
    email = Column(Unicode, nullable=False)
    date_joined = Column(DateTime, default=datetime.now())
    username = Column(Unicode, nullable=False, unique=True)
    district = Column(Unicode, nullable=False)
    address_id = Column(Integer, ForeignKey('buildings.id', ondelete='CASCADE'), nullable=False)

    def get_id(self):
        return (self.username)


class Building(base):
    __tablename__ = 'buildings'

    id = Column(Integer, primary_key=True)
    district = Column(Unicode)
    address = Column(Unicode)
    name = Column(Unicode)
    building_type = Column(Unicode)
    mpoly = Column(Geometry('MULTIPOLYGON'))

    building = relationship("User")

    def building_to_dict(self):
        return shapely.wkb.loads(self.mpoly)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        d = dict()
        d['id'] = self.id
        d['district'] = self.district
        d['address'] = self.address
        d['name'] = self.name
        d['building_type'] = self.building_type
        d['mpoly'] = self.building_to_dict()
        return str(d)


class Announcement(base):
    __tablename__ = 'announcements'

    id = Column(Integer, primary_key=True)
    text = Column(Unicode)
    date = Column(DateTime, default=datetime.now())
    price = Column(Numeric(precision=6, scale=2))
    building_id = Column(Integer, ForeignKey('buildings.id'))


class UserMessage(base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    sender = Column(Unicode, ForeignKey('users.username'))
    receiver = Column(Unicode, ForeignKey('users.username'))
    message = Column(Unicode)
    date_send = Column(DateTime, default=datetime.now())


# metadata.drop_all()   # comment this on first occassion
# metadata.create_all()
