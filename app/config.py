# app/config.py
import os
import secrets
import datetime

class Config:
    SECRET_KEY = os.environ.get('YPS9fscE9JuFE8Db7pQgvdDQCg2pSyCBfZGiY2KVEQoF2mrr98d9oVLE7A4GMybxbb76') or secrets.token_hex(16)
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('DazxPbWNbkAMWZaykrBQj9zvC5hWDFhhFrCLiFyvhN2FYXCm5JNsQa7eErqKKowA9VRsSbTQS5WWKXWsXNDcnpqFQjRgt') or secrets.token_hex(16)
    PROPAGATE_EXCEPTIONS = True

    # Login expiration
    # This cannot be timedelta object directly, so we define it here
    # It cannot also be defined inside the of the .env file as it needs to be a timedelta object
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=1)