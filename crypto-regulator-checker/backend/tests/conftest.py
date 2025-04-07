"""Test configuration and fixtures."""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.db.base import Base
from src.models.user import User
from src.models.document import Document

# Set test environment variables
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENV"] = "test"
os.environ["DEBUG"] = "true"

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def db_engine():
    """Create a new database engine for testing."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def db(db_engine) -> Session:
    """Create a new database session for a test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="test-password-hash"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Store original environment variables
    original_env = {
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        "ENV": os.environ.get("ENV"),
        "DEBUG": os.environ.get("DEBUG")
    }
    
    # Set test environment variables
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["ENV"] = "test"
    os.environ["DEBUG"] = "true"
    
    yield
    
    # Restore original environment variables
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value 