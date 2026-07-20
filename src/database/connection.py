from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from src.database.models import Base


def build_engine(db_url: str = "sqlite:///data/mirrorpace.db") -> Engine:
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine


def build_session(engine: Engine) -> Session:
    SessionFactory = sessionmaker(bind=engine)
    return SessionFactory()
