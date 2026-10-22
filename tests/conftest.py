import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import urlsafety
from app.database import Base
from app.models import Site


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()


@pytest.fixture
def site(db):
    s = Site(url="https://example.com", interval_minutes=5)
    db.add(s)
    db.commit()
    return s


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    """Tests never touch real DNS: every hostname resolves to a public address."""
    monkeypatch.setattr(urlsafety, "_resolve", lambda host, port: ["93.184.216.34"])
