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
    
    # Profile fields
    bio = db.Column(db.Text, nullable=True, default='')
    profile_picture = db.Column(db.String(500), nullable=True)
    favorite_genres = db.Column(db.String(500), nullable=True, default='')  # Comma-separated genres
    
    reviews = db.relationship('Review', backref='author', lazy=True)

    def set_password(self, password):
        # test if the password is over 8 characters
        if len(password) < 8:
            return False

        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        return True

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'bio': self.bio or '',
            'profile_picture': self.profile_picture,
            'favorite_genres': self.favorite_genres or ''
        }

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
    
    # Track who created the movie
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    creator = db.relationship('User', backref='created_movies', lazy=True)
    
    reviews = db.relationship('Review', backref='movie', lazy=True, cascade="all, delete-orphan")

    def average_rating(self):
        if not self.reviews:
            return "N/A"
        total = sum([r.rating for r in self.reviews])
        return round(total / len(self.reviews), 1)

    def to_dict(self):
        creator_info = None
        if self.creator:
            creator_info = {
                'id': self.creator.id,
                'username': self.creator.username,
                'profile_picture': self.creator.profile_picture
            }
        
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'image_url': self.image_url,
            'director': self.director,
            'cast': self.cast,
            'average_rating': self.average_rating(),
            'review_count': len(self.reviews),
            'creator': creator_info,
            'user_id': self.user_id
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
    likes = db.relationship('ReviewLike', backref='review', lazy=True, cascade="all, delete-orphan")

class ReviewLike(db.Model):
    __tablename__ = 'review_likes'
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_like = db.Column(db.Boolean, nullable=False)  # True for like, False for dislike
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='review_likes', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('review_id', 'user_id', name='unique_user_review_like'),)