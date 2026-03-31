from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'estela-job-tracker-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' 

# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    jobs = db.relationship('Job', backref='user', lazy=True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Applied')
    date_applied = db.Column(db.String(50))
    notes = db.Column(db.String(500))
    link = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---

# FIX: This is now the FIRST page people see
@app.route('/')
def login():
    """Login Page: This is now the root URL (/)"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        
    return render_template('login.html')

# FIX: The actual Job Tracker is now at /dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    """The Job Tracker: Only accessible after logging in."""
    jobs = Job.query.filter_by(user_id=current_user.id).all()
    stats = {
        'total': len(jobs),
        'applied': len([j for j in jobs if j.status == 'Applied']),
        'interview': len([j for j in jobs if j.status == 'Interview']),
        'offer': len([j for j in jobs if j.status == 'Offer']),
        'rejected': len([j for j in jobs if j.status == 'Rejected'])
    }
    return render_template('index.html', jobs=jobs, **stats)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=request.form['username'], password=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/add', methods=['POST'])
@login_required
def add_job():
    today = datetime.today().strftime('%Y-%m-%d')
    new_job = Job(
        company=request.form.get('company'),
        role=request.form.get('role'),
        status=request.form.get('status', 'Applied'),
        date_applied=request.form.get('date_applied') or today,
        notes=request.form.get('notes'),
        link=request.form.get('link'),
        user_id=current_user.id
    )
    db.session.add(new_job)
    db.session.commit()
    return redirect(url_for('dashboard')) # Updated to dashboard

@app.route('/delete/<int:job_id>')
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user_id == current_user.id:
        db.session.delete(job)
        db.session.commit()
    return redirect(url_for('dashboard')) # Updated to dashboard

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)