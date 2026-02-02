"""
Database initialization and management utilities
"""

from sqlalchemy import create_engine
from app.models import Base
from app.config import settings


def create_tables():
    """Create all database tables"""
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def drop_tables():
    """Drop all database tables (use with caution!)"""
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped successfully")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        create_tables()
    elif len(sys.argv) > 1 and sys.argv[1] == "drop":
        response = input("Are you sure you want to drop all tables? (yes/no): ")
        if response.lower() == "yes":
            drop_tables()
        else:
            print("Operation cancelled")
    else:
        print("Usage: python init_db.py [create|drop]")
