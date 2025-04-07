"""Script to set up test data for load testing."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.document import Document
from src.core.database import Base
from src.core.config import settings

# Create database engine using the same URL as the server
engine = create_engine(settings.DATABASE_URL)

# Create tables
Base.metadata.create_all(engine)

# Create session
Session = sessionmaker(bind=engine)
session = Session()

def setup_test_data():
    """Create test document for load testing."""
    # Check if test document already exists
    test_doc = session.query(Document).filter(Document.id == 1).first()
    if test_doc:
        # Update user_id to match JWT token
        test_doc.user_id = "1"  # Match the 'sub' claim in the JWT
        session.commit()
        print("Test document updated successfully")
    else:
        # Create test document with proper file path
        upload_dir = os.path.abspath(settings.UPLOAD_DIR)
        os.makedirs(upload_dir, exist_ok=True)
        test_file_path = os.path.join(upload_dir, 'test_document.pdf')
        
        # Create an empty test file if it doesn't exist
        if not os.path.exists(test_file_path):
            with open(test_file_path, 'wb') as f:
                f.write(b'Test PDF content')
        
        test_doc = Document(
            id=1,
            user_id="1",  # Match the 'sub' claim in the JWT
            filename='test_document.pdf',
            file_path=test_file_path,
            status='processed'
        )
        session.add(test_doc)
        session.commit()
        print("Test document created successfully")

if __name__ == '__main__':
    setup_test_data() 