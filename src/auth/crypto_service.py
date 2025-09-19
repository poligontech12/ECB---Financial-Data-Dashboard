"""
Database encryption service for ECB Financial Data Visualizer
Handles SQLite database encryption/decryption using PIN-derived keys
"""
import os
import shutil
import sqlite3
from pathlib import Path
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from utils.config import get_config
from utils.logging_config import get_logger

logger = get_logger(__name__)

class DatabaseCryptoService:
    """Service for encrypting and decrypting SQLite database files"""
    
    def __init__(self):
        self.config = get_config()
        self.database_path = self.config["paths"]["database_path"]
        self.encrypted_db_path = self.database_path.with_suffix('.db.encrypted')
        self.backup_db_path = self.database_path.with_suffix('.db.backup')
        
        # Fixed salt for consistency (in production, store this securely)
        self.salt = b'ecb_financial_visualizer_salt_2024'
        
        logger.info("Database encryption service initialized")
    
    def is_database_encrypted(self) -> bool:
        """
        Check if database is currently encrypted
        
        Returns:
            True if database is encrypted
        """
        try:
            # Check if encrypted file exists and original doesn't
            encrypted_exists = self.encrypted_db_path.exists()
            original_exists = self.database_path.exists()
            
            if encrypted_exists and not original_exists:
                return True
            elif original_exists and not encrypted_exists:
                return False
            elif not encrypted_exists and not original_exists:
                # No database exists yet
                return False
            else:
                # Both exist - something went wrong, prefer encrypted
                logger.warning("Both encrypted and unencrypted database files exist")
                return True
                
        except Exception as e:
            logger.error(f"Error checking database encryption status: {e}")
            return False
    
    def encrypt_database(self, pin: str) -> Tuple[bool, str]:
        """
        Encrypt the database file using PIN-derived key
        
        Args:
            pin: 6-digit PIN for encryption
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not self.database_path.exists():
                # No database to encrypt yet - this is normal for first run
                logger.info("No database file exists yet - will be created encrypted")
                return True, ""
            
            if self.is_database_encrypted():
                logger.info("Database is already encrypted")
                return True, ""
            
            # Create backup
            if not self._create_backup():
                return False, "Failed to create database backup"
            
            # Derive encryption key from PIN
            key = self._derive_key_from_pin(pin)
            fernet = Fernet(key)
            
            # Read and encrypt database file
            with open(self.database_path, 'rb') as f:
                plaintext_data = f.read()
            
            encrypted_data = fernet.encrypt(plaintext_data)
            
            # Write encrypted file
            with open(self.encrypted_db_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Remove original unencrypted file
            os.remove(self.database_path)
            
            logger.info("Database encrypted successfully")
            return True, ""
            
        except Exception as e:
            logger.error(f"Error encrypting database: {e}")
            self._restore_backup()
            return False, f"Encryption failed: {str(e)}"
    
    def decrypt_database(self, pin: str) -> Tuple[bool, str]:
        """
        Decrypt the database file using PIN-derived key
        
        Args:
            pin: 6-digit PIN for decryption
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not self.is_database_encrypted():
                logger.info("Database is not encrypted")
                return True, ""
            
            if not self.encrypted_db_path.exists():
                return False, "Encrypted database file not found"
            
            # Derive encryption key from PIN
            key = self._derive_key_from_pin(pin)
            fernet = Fernet(key)
            
            # Read and decrypt database file
            with open(self.encrypted_db_path, 'rb') as f:
                encrypted_data = f.read()
            
            try:
                decrypted_data = fernet.decrypt(encrypted_data)
            except Exception as decrypt_error:
                logger.error(f"Failed to decrypt database: {decrypt_error}")
                return False, "Invalid PIN - cannot decrypt database"
            
            # Write decrypted file
            with open(self.database_path, 'wb') as f:
                f.write(decrypted_data)
            
            # Verify the decrypted file is a valid SQLite database
            if not self._verify_sqlite_database():
                os.remove(self.database_path)
                return False, "Decrypted file is not a valid database"
            
            logger.info("Database decrypted successfully")
            return True, ""
            
        except Exception as e:
            logger.error(f"Error decrypting database: {e}")
            return False, f"Decryption failed: {str(e)}"
    
    def lock_database(self) -> Tuple[bool, str]:
        """
        Lock the database by removing the decrypted file
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if self.database_path.exists():
                os.remove(self.database_path)
                logger.info("Database locked (decrypted file removed)")
            return True, ""
        except Exception as e:
            logger.error(f"Error locking database: {e}")
            return False, f"Failed to lock database: {str(e)}"
    
    def _derive_key_from_pin(self, pin: str) -> bytes:
        """
        Derive encryption key from PIN using PBKDF2
        
        Args:
            pin: 6-digit PIN
            
        Returns:
            32-byte encryption key
        """
        pin_bytes = pin.encode('utf-8')
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,  # Good balance of security and performance
        )
        key = base64.urlsafe_b64encode(kdf.derive(pin_bytes))
        return key
    
    def _create_backup(self) -> bool:
        """Create backup of current database"""
        try:
            if self.database_path.exists():
                shutil.copy2(self.database_path, self.backup_db_path)
                logger.info("Database backup created")
            return True
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def _restore_backup(self) -> bool:
        """Restore database from backup"""
        try:
            if self.backup_db_path.exists():
                shutil.copy2(self.backup_db_path, self.database_path)
                logger.info("Database restored from backup")
                return True
            return False
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def _verify_sqlite_database(self) -> bool:
        """Verify that the file is a valid SQLite database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            # Check if we have the expected tables
            table_names = [table[0] for table in tables]
            expected_tables = ['financial_series', 'observations']
            
            if any(table in table_names for table in expected_tables):
                logger.info("Database verification successful")
                return True
            else:
                logger.warning("Database doesn't contain expected tables")
                return True  # Still a valid SQLite file, just empty
                
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return False
    
    def cleanup_backup(self) -> bool:
        """Clean up backup file"""
        try:
            if self.backup_db_path.exists():
                os.remove(self.backup_db_path)
                logger.info("Backup file cleaned up")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up backup: {e}")
            return False
    
    def get_database_status(self) -> dict:
        """Get status information about database files"""
        try:
            return {
                "encrypted_exists": self.encrypted_db_path.exists(),
                "decrypted_exists": self.database_path.exists(),
                "backup_exists": self.backup_db_path.exists(),
                "is_encrypted": self.is_database_encrypted(),
                "encrypted_size": self.encrypted_db_path.stat().st_size if self.encrypted_db_path.exists() else 0,
                "decrypted_size": self.database_path.stat().st_size if self.database_path.exists() else 0
            }
        except Exception as e:
            logger.error(f"Error getting database status: {e}")
            return {"error": str(e)}