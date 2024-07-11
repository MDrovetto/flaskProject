from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import sqlite3

app = Flask(__name__)

# Define the path for the SQLite database
db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def init_sqlite_db():
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES user (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS answer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        question_id INTEGER,
        user_id INTEGER,
        FOREIGN KEY (question_id) REFERENCES question (id),
        FOREIGN KEY (user_id) REFERENCES user (id)
    )
    ''')
    conn.commit()
    conn.close()

init_sqlite_db()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    senha = db.Column(db.String(150), nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('questions', lazy=True))

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    question = db.relationship('Question', backref=db.backref('answers', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('answers', lazy=True))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        new_user = User(nome=nome, email=email, senha=senha)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return f'Error registering user: {e}'
    return render_template('registrar.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        try:
            user = User.query.filter_by(email=email, senha=senha).first()
            if user:
                return redirect(url_for('dashboard', user_id=user.id))
            else:
                return 'Invalid credentials'
        except Exception as e:
            return f'Error logging in: {e}'
    return render_template('login.html')

@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    user = User.query.get(user_id)
    questions = Question.query.all()
    return render_template('dashboard.html', user=user, questions=questions)

@app.route('/nova_pergunta', methods=['GET', 'POST'])
def nova_pergunta():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user_id = request.form['user_id']

        # Debug statement to check the user_id
        print(f"user_id: {user_id}")

        new_question = Question(title=title, content=content, user_id=user_id)
        try:
            db.session.add(new_question)
            db.session.commit()
            return redirect(url_for('dashboard', user_id=user_id))
        except Exception as e:
            # Print the exception to debug
            print(f"Error: {e}")
            return 'Error creating question'
    user_id = request.args.get('user_id')
    return render_template('perguntas.html', user_id=user_id)

@app.route('/nova_resposta', methods=['GET', 'POST'])
def nova_resposta():
    if request.method == 'POST':
        content = request.form['content']
        question_id = request.form['question_id']
        user_id = request.form['user_id']

        # Debug statements to check question_id and user_id
        print(f"question_id: {question_id}, user_id: {user_id}")

        new_answer = Answer(content=content, question_id=question_id, user_id=user_id)
        try:
            db.session.add(new_answer)
            db.session.commit()
            return redirect(url_for('dashboard', user_id=user_id))
        except Exception as e:
            # Print the exception to debug
            print(f"Error: {e}")
            return 'Error creating answer'
    question_id = request.args.get('question_id')
    user_id = request.args.get('user_id')
    return render_template('respostas.html', question_id=question_id, user_id=user_id)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
