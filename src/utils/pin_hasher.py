"""
PIN Hashing Utility for ECB Financial Data Visualizer
Provides secure PIN hashing and verification using bcrypt
"""

import bcrypt


class PINHasher:
    """Secure PIN hashing utility using bcrypt"""
    
    @staticmethod
    def hash_pin(pin: str) -> str:
        """
        Hash a PIN using bcrypt with salt
        
        Args:
            pin: The plaintext PIN to hash
            
        Returns:
            The bcrypt hashed PIN as a string
        """
        # Convert PIN to bytes
        pin_bytes = pin.encode('utf-8')
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds for good security/performance balance
        hashed = bcrypt.hashpw(pin_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_pin(pin: str, hashed_pin: str) -> bool:
        """
        Verify a PIN against its hash
        
        Args:
            pin: The plaintext PIN to verify
            hashed_pin: The stored bcrypt hash
            
        Returns:
            True if PIN matches, False otherwise
        """
        try:
            # Convert to bytes
            pin_bytes = pin.encode('utf-8')
            hashed_bytes = hashed_pin.encode('utf-8')
            
            # Verify using bcrypt
            return bcrypt.checkpw(pin_bytes, hashed_bytes)
        except Exception:
            # Return False for any verification errors
            return False


def generate_pin_hash(pin: str) -> str:
    """
    Convenience function to generate a PIN hash
    Use this to generate hashes for configuration
    
    Args:
        pin: The PIN to hash (e.g., "112233")
        
    Returns:
        The bcrypt hash string
    """
    return PINHasher.hash_pin(pin)


if __name__ == "__main__":
    # Script to generate PIN hash for configuration
    test_pin = "112233"
    hashed = generate_pin_hash(test_pin)
    
    print("PIN Hash Generator")
    print("=================")
    print(f"PIN: {test_pin}")
    print(f"Hash: {hashed}")
    print(f"Verification: {PINHasher.verify_pin(test_pin, hashed)}")
    
    # Test with wrong PIN
    print(f"Wrong PIN test: {PINHasher.verify_pin('123456', hashed)}")