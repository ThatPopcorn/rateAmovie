# app/models.py
from datetime import datetime, timedelta
from .extensions import db, bcrypt
import jwt
from flask import current_app

class TokenBlacklist(db.Model):
    __tablename__ = 'token_blacklist'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    reviews = db.relationship('Review', backref='author', lazy=True)

    def set_password(self, password):
        # test if the password is over 8 characters
        if len(password) < 8:
            return False

        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        return True

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    release_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New Fields
    image_url = db.Column(db.String(500), nullable=True)
    director = db.Column(db.String(100), nullable=True)
    cast = db.Column(db.Text, nullable=True)
    
    reviews = db.relationship('Review', backref='movie', lazy=True, cascade="all, delete-orphan")

    def average_rating(self):
        if not self.reviews:
            return "N/A"
        total = sum([r.rating for r in self.reviews])
        return round(total / len(self.reviews), 1)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'image_url': self.image_url,
            'director': self.director,
            'cast': self.cast,
            'average_rating': self.average_rating(),
            'review_count': len(self.reviews)
        }

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    
    # Add relationship to access username easily
    user = db.relationship('User', backref='user_reviews', lazy=True)