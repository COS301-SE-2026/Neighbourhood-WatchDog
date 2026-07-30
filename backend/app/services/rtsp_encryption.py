from cryptography.fernet import Fernet
import os

fernet = Fernet(os.environ["RTSP_ENCRYPTION_KEY"])

def encrypt_rtsp_url(plaintext: str) -> str:
    return fernet.encrypt(plaintext.encode()).decode()

def decrypt_rtsp_url(ciphertext: str) -> str:
    return fernet.decrypt(ciphertext.encode()).decode()