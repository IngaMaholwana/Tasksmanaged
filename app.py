from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo_users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    tasks = db.relationship('Task', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    importance = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Task {self.title}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create all database tables
with app.app_context():
    db.create_all()

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Task routes
@app.route('/')
@login_required
def index():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.date_created).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    if request.method == 'POST':
        task_title = request.form['title']
        task_description = request.form['description']
        task_importance = request.form.get('importance', 1)

        try:
            task_importance = int(task_importance)
            if not 1 <= task_importance <= 4:
                task_importance = 1
        except ValueError:
            task_importance = 1

        new_task = Task(
            title=task_title,
            description=task_description,
            importance=task_importance,
            user_id=current_user.id
        )

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for('index'))
        except:
            flash('There was an issue adding your task')
            return redirect(url_for('index'))

@app.route('/update_task/<int:id>', methods=['POST'])
@login_required
def update_task(id):
    task = Task.query.get_or_404(id)
    
    # Verify task belongs to current user
    if task.user_id != current_user.id:
        flash('Unauthorized access to task')
        return redirect(url_for('index'))

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        
        try:
            task_importance = int(request.form['importance'])
            if 1 <= task_importance <= 4:
                task.importance = task_importance
        except ValueError:
            pass

        try:
            db.session.commit()
            return redirect(url_for('index'))
        except:
            flash('There was an issue updating your task')
            return redirect(url_for('index'))

@app.route('/delete_task/<int:id>', methods=['POST'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    
    # Verify task belongs to current user
    if task.user_id != current_user.id:
        flash('Unauthorized access to task')
        return redirect(url_for('index'))

    try:
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('index'))
    except:
        flash('There was an issue deleting your task')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)