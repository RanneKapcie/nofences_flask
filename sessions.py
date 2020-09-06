from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/nofences', echo=True)
Session = sessionmaker(bind=engine)
db_session = Session()


metadata = MetaData(engine)
base = declarative_base(metadata=metadata)