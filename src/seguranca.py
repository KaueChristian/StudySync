import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Deriva uma chave de criptografia segura usando PBKDF2
    """
    kdf = PBKDF2HMAC(
        algorithm = hashes.SHA256(),
        length = 32,
        salt = salt,
        iterations = 100000,
        backend = default_backend() 
    )
    return kdf.derive(password.encode())

def encrypt_data(password: str, email: str) -> tuple:
    """
    Criptografia dados com AES em modo GCM
    """
    salt = os.urandom(16)
    key = derive_key(password, salt)
    iv = os.urandom(12)
    
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend = default_backend()
    ).encryptor()
    
    encrypted_data = encryptor.update(email.decode()) + encryptor.finalize()
    return (salt, iv, encryptor.tag, encrypted_data)

def decrypt_data(password: str, encrypted_email: tuple) -> str:
    """
    Descriptografa dados criptografados com AES em modo GCM
    """
    salt, iv, tag, ciphertext = encrypted_email
    key = derive_key(password, salt)
    
    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend = default_backend()
    ).decryptor()
    
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
    return decrypted_data.decode()

