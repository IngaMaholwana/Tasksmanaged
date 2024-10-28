from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    importance = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Task {self.title}>'

# Create the database and tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    tasks = Task.query.order_by(Task.date_created).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add_task', methods=['POST'])
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
            importance=task_importance
        )

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding your task'

@app.route('/update_task/<int:id>', methods=['POST'])
def update_task(id):
    task = Task.query.get_or_404(id)

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
            return redirect('/')
        except:
            return 'There was an issue updating your task'

@app.route('/delete_task/<int:id>', methods=['POST'])
def delete_task(id):
    task_to_delete = Task.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was an issue deleting your task'



if __name__ == '__main__':
    app.run(debug=True)