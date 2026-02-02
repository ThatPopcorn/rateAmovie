# app/routes.py
from flask import Blueprint, request, jsonify, render_template_string
from datetime import datetime
from .extensions import db
from .models import Movie, Review, User
from flask_jwt_extended import jwt_required, get_jwt_identity

main_bp = Blueprint('main', __name__)

# ==========================================
#  THE FRONTEND (HTML/JS/CSS)
# ==========================================

HTML_LAYOUT = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>rateAmovie</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #121212; color: #ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .card { background-color: #1f1f1f; color: white; border: none; margin-bottom: 20px; border-radius: 12px; transition: transform 0.2s; }
        .card:hover { transform: translateY(-4px); box-shadow: 0 8px 16px rgba(255,193,7,0.2); }
        .movie-card { cursor: pointer; }
        .text-warning { color: #ffc107 !important; }
        .form-control, .form-select { background-color: #2b2b2b; border: 1px solid #444; color: white; border-radius: 8px; }
        .form-control:focus, .form-select:focus { background-color: #2b2b2b; color: white; border-color: #ffc107; box-shadow: 0 0 0 0.2rem rgba(255,193,7,0.25); }
        .star-rating { font-size: 2rem; cursor: pointer; color: #444; user-select: none; }
        .star-rating .star { transition: color 0.2s; display: inline-block; }
        .star-rating .star.filled { color: #ffc107; }
        .star-rating .star:hover, .star-rating .star:hover ~ .star { color: #ffc107; }
        .review-card { background-color: #2a2a2a; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 3px solid #ffc107; }
        .badge-rating { background-color: #ffc107; color: #000; padding: 0.5rem 0.8rem; border-radius: 8px; font-size: 1.1rem; font-weight: bold; }
        .movie-poster { width: 100%; height: 300px; background: linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 4rem; color: #444; margin-bottom: 1rem; object-fit: cover; }
        .btn { border-radius: 8px; font-weight: 500; }
        .search-box { background-color: #2b2b2b; border: 1px solid #444; border-radius: 25px; padding: 0.5rem 1rem; }
        .empty-state { text-align: center; padding: 3rem; color: #666; }
        .empty-state-icon { font-size: 4rem; margin-bottom: 1rem; }
        textarea.form-control { resize: vertical; min-height: 100px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-black py-3 shadow">
        <div class="container">
            <a class="navbar-brand fw-bold text-warning fs-4" href="/">🎬 rateAmovie</a>
            <div class="d-flex align-items-center" id="nav-actions">
                <!-- JS fills this -->
            </div>
        </div>
    </nav>

    <div class="container mt-4 pb-5">
        {{ content|safe }}
    </div>

    <script>
        // --- Auth Logic ---
        function saveToken(token, username) {
            localStorage.setItem('access_token', token);
            localStorage.setItem('username', username);
            window.location.href = '/';
        }

        function logout() {
            localStorage.clear();
            window.location.href = '/login';
        }

        function isLoggedIn() {
            return !!localStorage.getItem('access_token');
        }

        async function authFetch(url, options = {}) {
            const token = localStorage.getItem('access_token');
            const headers = { 'Content-Type': 'application/json', ...options.headers };
            if (token) headers['Authorization'] = `Bearer ${token}`;
            
            const res = await fetch(url, { ...options, headers });
            if (res.status === 401) {
                alert('Session expired. Please login again.');
                logout();
            }
            return res;
        }

        function requireAuth() {
            if (!isLoggedIn()) {
                alert('Please login to access this page');
                window.location.href = '/login';
                return false;
            }
            return true;
        }

        // --- Star Rating Component ---
        function createStarRating(containerId, initialRating = 0, onChange = null) {
            const container = document.getElementById(containerId);
            let currentRating = initialRating;
            
            container.innerHTML = '';
            container.className = 'star-rating';
            
            for(let i = 5; i >= 1; i--) {
                const star = document.createElement('span');
                star.className = 'star';
                star.innerHTML = '★';
                star.dataset.rating = i;
                
                if(i <= currentRating) star.classList.add('filled');
                
                if(onChange) {
                    star.onclick = () => {
                        currentRating = i;
                        updateStars();
                        onChange(i);
                    };
                }
                
                container.appendChild(star);
            }
            
            function updateStars() {
                container.querySelectorAll('.star').forEach(s => {
                    s.classList.toggle('filled', parseInt(s.dataset.rating) <= currentRating);
                });
            }
            
            return { getRating: () => currentRating };
        }

        function displayStars(rating) {
            let stars = '';
            for(let i = 1; i <= 5; i++) {
                stars += `<span class="text-warning">${i <= rating ? '★' : '☆'}</span>`;
            }
            return stars;
        }

        // --- Navbar Updates ---
        document.addEventListener('DOMContentLoaded', () => {
            const nav = document.getElementById('nav-actions');
            if (isLoggedIn()) {
                const user = localStorage.getItem('username');
                nav.innerHTML = `
                    <a href="/create-movie" class="btn btn-outline-success btn-sm me-3">+ Add Movie</a>
                    <span class="text-secondary me-3">Hello, <strong>${user}</strong></span>
                    <button onclick="logout()" class="btn btn-outline-danger btn-sm">Logout</button>
                `;
            } else {
                nav.innerHTML = `
                    <a href="/login" class="btn btn-outline-light btn-sm me-2">Login</a>
                    <a href="/register" class="btn btn-warning btn-sm">Register</a>
                `;
            }
        });
    </script>
</body>
</html>
"""

PAGE_HOME = HTML_LAYOUT.replace('{{ content|safe }}', r"""
<div class="row mb-4">
    <div class="col-md-6">
        <h2 class="mb-0">Top Rated Movies</h2>
    </div>
    <div class="col-md-6">
        <div class="d-flex gap-2">
            <input type="text" id="search" class="form-control search-box" placeholder="🔍 Search movies...">
            <select id="sort" class="form-select" style="max-width: 200px;">
                <option value="rating">Top Rated</option>
                <option value="title">Title (A-Z)</option>
                <option value="recent">Recently Added</option>
            </select>
        </div>
    </div>
</div>

<div id="movie-list" class="row"></div>

<script>
    let allMovies = [];
    
    async function loadMovies() {
        const res = await fetch('/api/movies');
        allMovies = await res.json();
        displayMovies(allMovies);
    }
    
    function displayMovies(movies) {
        const container = document.getElementById('movie-list');
        
        if(movies.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🎬</div>
                    <h4>No movies found</h4>
                    <p class="text-secondary">Be the first to add a movie!</p>
                    ${isLoggedIn() ? '<a href="/create-movie" class="btn btn-warning mt-3">Add Movie</a>' : ''}
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        movies.forEach(m => {
            const avgRating = m.average_rating || 0;
            const reviewCount = m.review_count || 0;
            
            // Image handling logic
            let imageHtml = '<div class="movie-poster">🎬</div>';
            if(m.image_url) {
                imageHtml = `<img src="${m.image_url}" class="movie-poster" style="object-fit: cover;" alt="${m.title}">`;
            }

            container.innerHTML += `
                <div class="col-md-4 col-lg-3">
                    <div class="card p-3 h-100 movie-card" onclick="window.location.href='/movie/${m.id}'">
                        ${imageHtml}
                        <h5 class="mb-2 text-truncate">${m.title}</h5>
                        <div class="d-flex align-items-center mb-2">
                            <span class="badge-rating me-2">★ ${typeof avgRating === 'number' ? avgRating.toFixed(1) : 'N/A'}</span>
                            <span class="small text-secondary">By ${m.director || 'Unknown'}</span>
                        </div>
                        <p class="small text-secondary mb-1">Released: ${m.release_date}</p>
                        <p class="small text-light mb-0">${m.description.substring(0, 80)}${m.description.length > 80 ? '...' : ''}</p>
                    </div>
                </div>
            `;
        });
    }
    
    function filterAndSort() {
        const searchTerm = document.getElementById('search').value.toLowerCase();
        const sortBy = document.getElementById('sort').value;
        
        let filtered = allMovies.filter(m => 
            m.title.toLowerCase().includes(searchTerm) || 
            m.description.toLowerCase().includes(searchTerm)
        );
        
        filtered.sort((a, b) => {
            if(sortBy === 'rating') return (b.average_rating || 0) - (a.average_rating || 0);
            if(sortBy === 'title') return a.title.localeCompare(b.title);
            if(sortBy === 'recent') return b.id - a.id;
            return 0;
        });
        
        displayMovies(filtered);
    }
    
    document.getElementById('search').addEventListener('input', filterAndSort);
    document.getElementById('sort').addEventListener('change', filterAndSort);
    
    loadMovies();
</script>
""")

PAGE_MOVIE_DETAIL = HTML_LAYOUT.replace('{{ content|safe }}', r"""
<div class="row">
    <div class="col-md-4">
        <div class="card p-4">
            <div id="poster-container" class="mb-3">
                <div class="movie-poster">🎬</div>
            </div>
            
            <h2 id="movie-title" class="mb-2"></h2>
            
            <div class="d-flex align-items-center mb-3">
                <span id="avg-rating" class="badge-rating me-2"></span>
                <span id="review-count" class="small text-secondary"></span>
            </div>
            
            <div class="mb-3">
                <p class="small text-secondary mb-1"><strong>Director</strong></p>
                <p id="director" class="text-white"></p>
            </div>
            
            <div class="mb-3">
                <p class="small text-secondary mb-1"><strong>Cast</strong></p>
                <p id="cast" class="text-white small"></p>
            </div>

            <p class="small text-secondary mb-1"><strong>Released</strong></p>
            <p id="release-date" class="text-white"></p>
        </div>
    </div>
    
    <div class="col-md-8">
        <div class="card p-4 mb-4">
            <h4 class="mb-3 text-warning">Synopsis</h4>
            <p id="description" class="text-light" style="line-height: 1.6;"></p>
        </div>

        <div class="card p-4 mb-4" id="review-form-section" style="display: none;">
            <h4 class="mb-3">Write a Review</h4>
            <label class="mb-2">Your Rating</label>
            <div id="rating-input" class="mb-3"></div>
            <label class="mb-2">Your Review</label>
            <textarea id="review-content" class="form-control mb-3" placeholder="Share your thoughts about this movie..."></textarea>
            <button onclick="submitReview()" class="btn btn-warning">Submit Review</button>
            <p id="review-msg" class="mt-2"></p>
        </div>
        
        <h4 class="mb-3">Reviews</h4>
        <div id="reviews-list"></div>
    </div>
</div>

<script>
    const movieId = window.location.pathname.split('/')[2];
    let ratingWidget = null;
    
    async function loadMovieDetails() {
        const res = await fetch(`/api/movies/${movieId}`);
        if(!res.ok) {
            alert('Movie not found');
            window.location.href = '/';
            return;
        }
        
        const movie = await res.json();
        
        // Populate text fields
        document.getElementById('movie-title').textContent = movie.title;
        const rating = movie.average_rating !== "N/A" ? parseFloat(movie.average_rating).toFixed(1) : "N/A";
        document.getElementById('avg-rating').textContent = `★ ${rating}`;
        
        // Handle image
        if(movie.image_url) {
            document.getElementById('poster-container').innerHTML = 
                `<img src="${movie.image_url}" style="width:100%; border-radius:12px; box-shadow:0 5px 15px rgba(0,0,0,0.5);">`;
        }

        document.getElementById('director').textContent = movie.director || 'Unknown';
        document.getElementById('cast').textContent = movie.cast || 'Unknown';
        document.getElementById('release-date').textContent = movie.release_date;
        document.getElementById('description').textContent = movie.description;
        
        if(isLoggedIn()) {
            document.getElementById('review-form-section').style.display = 'block';
            ratingWidget = createStarRating('rating-input', 0, (rating) => {});
        }
    }
    
    async function loadReviews() {
        const res = await fetch(`/api/movies/${movieId}/reviews`);
        const reviews = await res.json();
        const container = document.getElementById('reviews-list');
        
        if(reviews.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding: 1rem;">
                    <p class="mb-0">No reviews yet. Be the first to review this movie!</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        reviews.forEach(r => {
            container.innerHTML += `
                <div class="review-card">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <strong>${r.username}</strong>
                            <div class="text-warning mt-1">${displayStars(r.rating)}</div>
                        </div>
                        <small class="text-secondary">${new Date(r.created_at).toLocaleDateString()}</small>
                    </div>
                    <p class="mb-0 text-light">${r.content}</p>
                </div>
            `;
        });
    }
    
    async function submitReview() {
        if(!requireAuth()) return;
        
        const rating = ratingWidget.getRating();
        const content = document.getElementById('review-content').value.trim();
        
        if(rating === 0) {
            document.getElementById('review-msg').innerHTML = '<span class="text-danger">Please select a rating</span>';
            return;
        }
        
        if(!content) {
            document.getElementById('review-msg').innerHTML = '<span class="text-danger">Please write a review</span>';
            return;
        }
        
        const res = await authFetch(`/api/movies/${movieId}/rate`, {
            method: 'POST',
            body: JSON.stringify({ rating, content })
        });
        
        const data = await res.json();
        
        if(res.ok) {
            document.getElementById('review-content').value = '';
            ratingWidget = createStarRating('rating-input', 0, (rating) => {});
            document.getElementById('review-msg').innerHTML = '<span class="text-success">Review submitted successfully!</span>';
            setTimeout(() => location.reload(), 1500);
        } else {
            document.getElementById('review-msg').innerHTML = `<span class="text-danger">${data.message || 'Error submitting review'}</span>`;
        }
    }
    
    loadMovieDetails();
    loadReviews();
</script>
""")

PAGE_CREATE = HTML_LAYOUT.replace('{{ content|safe }}', r"""
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card p-4">
            <h3 class="mb-4">Add a New Movie</h3>
            
            <div class="row">
                <div class="col-md-6">
                    <label class="mb-1 fw-bold">Title <span class="text-danger">*</span></label>
                    <input type="text" id="title" class="form-control mb-3" placeholder="e.g. The Matrix">
                </div>
                <div class="col-md-6">
                    <label class="mb-1 fw-bold">Release Date <span class="text-danger">*</span></label>
                    <input type="date" id="date" class="form-control mb-3">
                </div>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <label class="mb-1 fw-bold">Director</label>
                    <input type="text" id="director" class="form-control mb-3" placeholder="e.g. Christopher Nolan">
                </div>
                <div class="col-md-6">
                    <label class="mb-1 fw-bold">Poster Image URL</label>
                    <input type="url" id="image" class="form-control mb-3" placeholder="https://image.tmdb.org/...">
                </div>
            </div>

            <label class="mb-1 fw-bold">Cast (Comma separated)</label>
            <input type="text" id="cast" class="form-control mb-3" placeholder="e.g. Keanu Reeves, Laurence Fishburne">
            
            <label class="mb-1 fw-bold">Description <span class="text-danger">*</span></label>
            <textarea id="desc" class="form-control mb-3" rows="4" placeholder="Brief plot summary..."></textarea>
            
            <button onclick="submitMovie()" class="btn btn-warning w-100 py-2">Create Movie</button>
            <p id="msg" class="text-center mt-2"></p>
        </div>
    </div>
</div>
<script>
    async function submitMovie() {
        const payload = {
            title: document.getElementById('title').value.trim(),
            release_date: document.getElementById('date').value.trim(),
            description: document.getElementById('desc').value.trim(),
            director: document.getElementById('director').value.trim(),
            image_url: document.getElementById('image').value.trim(),
            cast: document.getElementById('cast').value.trim()
        };

        if(!payload.title || !payload.release_date || !payload.description) {
            document.getElementById('msg').innerHTML = '<span class="text-danger">Title, Date, and Description are required</span>';
            return;
        }

        const res = await authFetch('/api/movies', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            document.getElementById('msg').innerHTML = '<span class="text-success">Movie created successfully!</span>';
            setTimeout(() => window.location.href = '/', 1000);
        } else {
            document.getElementById('msg').innerHTML = `<span class="text-danger">${data.message || "Error creating movie"}</span>`;
        }
    }
</script>
""")

PAGE_LOGIN = HTML_LAYOUT.replace('{{ content|safe }}', r"""
<div class="row justify-content-center">
    <div class="col-md-4">
        <div class="card p-4">
            <h3 class="mb-4 text-center">Login</h3>
            <input type="email" id="email" class="form-control mb-3" placeholder="Email">
            <input type="password" id="pw" class="form-control mb-3" placeholder="Password">
            <button onclick="doLogin()" class="btn btn-warning w-100 py-2">Login</button>
            <p id="err" class="text-danger mt-3 text-center"></p>
            <p class="text-center mt-3 mb-0">
                <small class="text-secondary">Don't have an account? <a href="/register" class="text-warning">Register</a></small>
            </p>
        </div>
    </div>
</div>
<script>
    async function doLogin() {
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('pw').value;
        
        if(!email || !password) {
            document.getElementById('err').innerText = 'Please fill in all fields';
            return;
        }
        
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ email, password })
        });
        
        const data = await res.json();
        if(res.ok) {
            saveToken(data.access_token, data.username);
        } else {
            document.getElementById('err').innerText = data.message || 'Login failed';
        }
    }
    
    document.getElementById('pw').addEventListener('keypress', (e) => {
        if(e.key === 'Enter') doLogin();
    });
</script>
""")

PAGE_REGISTER = HTML_LAYOUT.replace('{{ content|safe }}', r"""
<div class="row justify-content-center">
    <div class="col-md-4">
        <div class="card p-4">
            <h3 class="mb-4 text-center">Register</h3>
            <input type="text" id="user" class="form-control mb-3" placeholder="Username">
            <input type="email" id="email" class="form-control mb-3" placeholder="Email">
            <input type="password" id="pw" class="form-control mb-3" placeholder="Password">
            <button onclick="doReg()" class="btn btn-warning w-100 py-2">Sign Up</button>
            <p id="msg" class="mt-3 text-center"></p>
            <p class="text-center mt-3 mb-0">
                <small class="text-secondary">Already have an account? <a href="/login" class="text-warning">Login</a></small>
            </p>
        </div>
    </div>
</div>
<script>
    async function doReg() {
        const username = document.getElementById('user').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('pw').value;
        
        if(!username || !email || !password) {
            document.getElementById('msg').innerHTML = '<span class="text-danger">Please fill in all fields</span>';
            return;
        }
        
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await res.json();
        if(res.ok) {
            document.getElementById('msg').innerHTML = '<span class="text-success">' + data.message + '</span>';
            setTimeout(() => window.location.href='/login', 1500);
        } else {
            document.getElementById('msg').innerHTML = '<span class="text-danger">' + data.message + '</span>';
        }
    }
</script>
""")

# ==========================================
#  WEB ROUTES
# ==========================================

@main_bp.route('/')
def home(): return render_template_string(PAGE_HOME)

@main_bp.route('/login')
def login_page(): return render_template_string(PAGE_LOGIN)

@main_bp.route('/register')
def register_page(): return render_template_string(PAGE_REGISTER)

@main_bp.route('/create-movie')
def create_movie_page(): return render_template_string(PAGE_CREATE)

@main_bp.route('/movie/<int:movie_id>')
def movie_detail_page(movie_id): return render_template_string(PAGE_MOVIE_DETAIL)


# ==========================================
#  API ROUTES
# ==========================================

@main_bp.route('/api/movies', methods=['GET'])
def get_movies():
    movies = Movie.query.all()
    return jsonify([movie.to_dict() for movie in movies]), 200

@main_bp.route('/api/movies/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return jsonify(movie.to_dict()), 200

@main_bp.route('/api/movies/<int:movie_id>/reviews', methods=['GET'])
def get_movie_reviews(movie_id):
    Movie.query.get_or_404(movie_id)  # Ensure movie exists
    reviews = Review.query.filter_by(movie_id=movie_id).order_by(Review.created_at.desc()).all()
    return jsonify([{
        'id': r.id,
        'rating': r.rating,
        'content': r.content,
        'username': r.user.username,
        'created_at': r.created_at.isoformat()
    } for r in reviews]), 200

@main_bp.route('/api/movies', methods=['POST'])
@jwt_required() # Ensure user is logged in with a valid JWT
def create_movie_api():
    try:
        data = request.get_json()
        
        # 1. Handle Date Parsing
        date_str = data.get('release_date')
        release_date_obj = None
        if date_str:
            try:
                # HTML input type="date" returns YYYY-MM-DD
                release_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

        # 2. Create Movie with new fields
        new_movie = Movie(
            title=data['title'],
            description=data.get('description', ''),
            release_date=release_date_obj,
            image_url=data.get('image_url', ''), 
            director=data.get('director', ''),   
            cast=data.get('cast', '')            
        )

        db.session.add(new_movie)
        db.session.commit()
        return jsonify({"message": "Movie added successfully", "movie": new_movie.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error adding movie: {str(e)}"}), 500

@main_bp.route('/api/movies/<int:movie_id>/rate', methods=['POST'])
@jwt_required() # Ensure user is logged in with a valid JWT
def rate_movie(movie_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    Movie.query.get_or_404(movie_id)  # Ensure movie exists
    
    # Check if user already reviewed this movie
    existing_review = Review.query.filter_by(user_id=current_user_id, movie_id=movie_id).first()
    if existing_review:
        return jsonify({"message": "You have already reviewed this movie"}), 400
    
    if not data.get('rating') or not data.get('content'):
        return jsonify({"message": "Rating and content are required"}), 400
    
    if not (1 <= data['rating'] <= 5):
        return jsonify({"message": "Rating must be between 1 and 5"}), 400
    
    review = Review(
        rating=data['rating'],
        content=data['content'],
        user_id=current_user_id,
        movie_id=movie_id
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({"message": "Review added successfully"}), 201