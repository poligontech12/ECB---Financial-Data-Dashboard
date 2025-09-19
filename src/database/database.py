"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from contextlib import contextmanager
from typing import Generator

from utils.config import get_config
from utils.logging_config import get_logger
from database.models import Base

logger = get_logger(__name__)

class DatabaseManager:
    """Manages database connection and sessions"""
    
    def __init__(self):
        self.config = get_config()
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database engine and session factory"""
        try:
            # Get database configuration
            db_config = self.config["database"]
            
            # Create engine
            self.engine = create_engine(
                db_config["sqlite_url"],
                echo=db_config["echo"],
                pool_pre_ping=db_config["pool_pre_ping"]
            )
            
            # Enable foreign key constraints for SQLite
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                if 'sqlite' in str(dbapi_connection):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            self.create_tables()
            
            logger.info(f"Database initialized: {db_config['sqlite_url']}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_session() as session:
                # Simple query to test connection
                result = session.execute(text("SELECT 1")).fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """Get database information"""
        try:
            with self.get_session() as session:
                # Get database file size if SQLite
                db_path = self.config["paths"]["database_path"]
                file_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
                
                # Count tables
                tables = Base.metadata.tables.keys()
                
                return {
                    "type": "SQLite",
                    "path": str(db_path),
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "tables": list(tables),
                    "table_count": len(tables)
                }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}

# Global database manager instance
db_manager = DatabaseManager()

def get_db_session():
    """Get database session (convenience function)"""
    return db_manager.get_session()

def init_database():
    """Initialize database (called at startup)"""
    try:
        db_manager.create_tables()
        logger.info("Database initialization completed")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
