from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import hashlib
import os
from datetime import datetime
import json
import csv
from sentiment_analyzer import SentimentAnalyzer
from analytics import Analytics

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

DATABASE = 'restaurant_reviews.db'
analyzer = SentimentAnalyzer()
analytics_engine = Analytics()

# Custom Jinja2 filter for JSON parsing
@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value) if value else []
    except:
        return []

# Database initialization
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Restaurants table
    c.execute('''CREATE TABLE IF NOT EXISTS restaurants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        cuisine TEXT,
        location TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Reviews table
    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        restaurant_id INTEGER,
        review_text TEXT NOT NULL,
        rating INTEGER CHECK(rating >= 1 AND rating <= 5),
        sentiment TEXT,
        sentiment_score REAL,
        keywords TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
    )''')
    
    # Create default admin user if not exists
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)",
                  ('admin', admin_password, 'admin@restaurant.com', 1))
    
    # Load restaurants from CSV database if table is empty
    c.execute("SELECT COUNT(*) FROM restaurants")
    if c.fetchone()[0] == 0:
        csv_file = 'database.csv'
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                restaurants_to_add = []
                seen_names = set()
                duplicates_skipped = 0
                
                for row in reader:
                    name = row['names'].strip()
                    
                    # Skip duplicates
                    if name in seen_names:
                        duplicates_skipped += 1
                        continue
                    
                    seen_names.add(name)
                    cuisine = row['cuisine'].strip()
                    rating = row['ratings'].strip()
                    location = f"Rating: {rating}" if rating and rating not in ['New', '-', ''] else "Not Rated"
                    restaurants_to_add.append((name, cuisine, location))
                
                # Insert all unique restaurants
                c.executemany("INSERT INTO restaurants (name, cuisine, location) VALUES (?, ?, ?)", 
                              restaurants_to_add)
                print(f"Successfully loaded {len(restaurants_to_add)} restaurants from database.csv")
                if duplicates_skipped > 0:
                    print(f"Skipped {duplicates_skipped} duplicate restaurant names")
        else:
            # Fallback to sample restaurants if CSV not found
            print("Warning: database.csv not found, using sample restaurants")
            sample_restaurants = [
                ('The Golden Fork', 'Italian', 'Downtown'),
                ('Spice Paradise', 'Indian', 'Midtown'),
                ('Sushi Heaven', 'Japanese', 'Uptown'),
                ('Burger Blast', 'American', 'West End'),
                ('La Bella Pizza', 'Italian', 'Downtown')
            ]
            c.executemany("INSERT INTO restaurants (name, cuisine, location) VALUES (?, ?, ?)", 
                          sample_restaurants)
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        
        conn = get_db()
        c = conn.cursor()
        
        try:
            hashed_pw = hash_password(password)
            c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                     (username, hashed_pw, email))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and user['password'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Get all restaurants
    c.execute("SELECT * FROM restaurants ORDER BY name")
    restaurants = c.fetchall()
    
    # Get user's recent reviews
    c.execute("""SELECT r.*, res.name as restaurant_name 
                 FROM reviews r 
                 JOIN restaurants res ON r.restaurant_id = res.id 
                 WHERE r.user_id = ? 
                 ORDER BY r.created_at DESC LIMIT 5""", (session['user_id'],))
    recent_reviews = c.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         restaurants=restaurants, 
                         recent_reviews=recent_reviews)

@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        restaurant_id = request.form['restaurant_id']
        review_text = request.form['review_text']
        rating = int(request.form['rating'])
        
        # Analyze sentiment
        sentiment_result = analyzer.analyze(review_text)
        
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO reviews 
                    (user_id, restaurant_id, review_text, rating, sentiment, sentiment_score, keywords)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                 (session['user_id'], restaurant_id, review_text, rating,
                  sentiment_result['sentiment'], sentiment_result['score'],
                  json.dumps(sentiment_result['keywords'])))
        conn.commit()
        conn.close()
        
        flash('Review added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # GET request
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM restaurants ORDER BY name")
    restaurants = c.fetchall()
    conn.close()
    
    return render_template('add_review.html', restaurants=restaurants)

@app.route('/restaurant/<int:restaurant_id>')
def restaurant_details(restaurant_id):
    conn = get_db()
    c = conn.cursor()
    
    # Get restaurant info
    c.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,))
    restaurant = c.fetchone()
    
    # Get all reviews for this restaurant
    c.execute("""SELECT r.*, u.username 
                 FROM reviews r 
                 JOIN users u ON r.user_id = u.id 
                 WHERE r.restaurant_id = ? 
                 ORDER BY r.created_at DESC""", (restaurant_id,))
    reviews = c.fetchall()
    
    conn.close()
    
    # Calculate statistics
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        for r in reviews:
            sentiment_counts[r['sentiment']] += 1
    else:
        avg_rating = 0
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    
    return render_template('restaurant_details.html',
                         restaurant=restaurant,
                         reviews=reviews,
                         avg_rating=avg_rating,
                         sentiment_counts=sentiment_counts)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Overall statistics
    c.execute("SELECT COUNT(*) as total FROM reviews")
    total_reviews = c.fetchone()['total']
    
    c.execute("SELECT COUNT(*) as total FROM restaurants")
    total_restaurants = c.fetchone()['total']
    
    c.execute("SELECT COUNT(*) as total FROM users WHERE is_admin = 0")
    total_users = c.fetchone()['total']
    
    # Sentiment distribution
    c.execute("""SELECT sentiment, COUNT(*) as count 
                 FROM reviews 
                 GROUP BY sentiment""")
    sentiment_dist = c.fetchall()
    
    # Top rated restaurants
    c.execute("""SELECT res.name, AVG(r.rating) as avg_rating, COUNT(r.id) as review_count
                 FROM restaurants res
                 LEFT JOIN reviews r ON res.id = r.restaurant_id
                 GROUP BY res.id
                 HAVING review_count > 0
                 ORDER BY avg_rating DESC
                 LIMIT 5""")
    top_restaurants = c.fetchall()
    
    # Worst rated restaurants
    c.execute("""SELECT res.name, AVG(r.rating) as avg_rating, COUNT(r.id) as review_count
                 FROM restaurants res
                 LEFT JOIN reviews r ON res.id = r.restaurant_id
                 GROUP BY res.id
                 HAVING review_count > 0
                 ORDER BY avg_rating ASC
                 LIMIT 5""")
    worst_restaurants = c.fetchall()
    
    # Get all reviews for analysis
    c.execute("SELECT * FROM reviews")
    all_reviews = c.fetchall()
    
    conn.close()
    
    # Generate analytics
    analytics_data = analytics_engine.generate_insights(all_reviews)
    
    return render_template('admin_dashboard.html',
                         total_reviews=total_reviews,
                         total_restaurants=total_restaurants,
                         total_users=total_users,
                         sentiment_dist=sentiment_dist,
                         top_restaurants=top_restaurants,
                         worst_restaurants=worst_restaurants,
                         analytics=analytics_data)

@app.route('/api/sentiment_analysis', methods=['POST'])
def api_sentiment_analysis():
    """API endpoint for real-time sentiment analysis"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = analyzer.analyze(text)
    return jsonify(result)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
