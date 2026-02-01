# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions here
# create initial instances without app context e.g.
# db is an instance of SQLAlchemy
# jwt is an instance of JWTManager, etc.
db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
ma = Marshmallow()
migrate = Migrate()

# Rate limiting (Stored in memory for dev)
limiter = Limiter(key_func=get_remote_address)