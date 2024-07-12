from sqlite3 import IntegrityError
from flask import Flask, render_template, request, redirect, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user

app = Flask(__name__)

# Define the path for the SQLite database
db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecret'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(150), nullable=False)
    perguntas = db.relationship('Question', backref='autor', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    categorias = db.relationship('Category', secondary='question_category', lazy='subquery',
        backref=db.backref('question_categorias', lazy=True))
    tags = db.relationship('Tag', secondary='question_tag', lazy='subquery',
        backref=db.backref('question_tags', lazy=True))
    answers = db.relationship('Answer', backref='question', lazy=True)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='answers', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

question_category = db.Table('question_category',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

question_tag = db.Table('question_tag',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class QuestionForm(FlaskForm):
    titulo = StringField('Título', validators=[DataRequired()])
    conteudo = TextAreaField('Conteúdo', validators=[DataRequired()])
    categorias = SelectMultipleField('Categorias', coerce=int, choices=[])
    tags = SelectMultipleField('Tags', coerce=int, choices=[])
    submit = SubmitField('Postar')

def create_initial_data():
    # Criar categorias
    categorias = ['Recursos Humanos', 'Finanças', 'Tecnologia da Informação (TI)', 'Marketing', 'Duvidas',"Geral"]
    for cat in categorias:
        # Verificar se a categoria já existe
        if not Category.query.filter_by(name=cat).first():
            categoria = Category(name=cat)
            db.session.add(categoria)

    # Criar tags
    tags = ['Contratação', 'Treinamento', 'Benefícios', 'Férias', 'Avaliação de Desempenho', 'Orçamento','Pagamentos','Suporte Técnico', 'Segurança', 'Software', 'Hardware', 'Redes',
            'Redes Sociais', 'Publicidade','Metas', 'Relacionamento com o Cliente','Planejamento', 'Reuniões', 'Documentação', 'Políticas Internas',
            'Suporte', 'Reclamações', 'Feedback', 'Satisfação do Cliente', 'Service Desk',
            'Contratos']
    for tag in tags:
        # Verificar se a tag já existe
        if not Tag.query.filter_by(name=tag).first():
            etiqueta = Tag(name=tag)
            db.session.add(etiqueta)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        print("Alguma entrada já existe no banco de dados.")

def setup():
    db.create_all()
    create_initial_data()

# Initialize the database and create initial data
with app.app_context():
    setup()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        # Verificar se o email já existe
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return 'Email já cadastrado, tente outro email.'

        # Gerar o hash da senha
        hashed_password = generate_password_hash(senha)
        new_user = User(nome=nome, email=email, senha=hashed_password)
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
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.senha, senha):
                login_user(user)
                return redirect(url_for('dashboard', user_id=user.id))
            else:
                return 'Usuario Invalido'
        except Exception as e:
            return f'Error logging in: {e}'
    return render_template('login.html')

@app.route('/dashboard/<int:user_id>')
@login_required
def dashboard(user_id):
    user = User.query.get_or_404(user_id)
    # Buscar todas as perguntas em vez de apenas as perguntas do usuário logado
    perguntas = Question.query.all()
    return render_template('dashboard.html', user=user, perguntas=perguntas)


@app.route('/nova_pergunta', methods=['GET', 'POST'])
@login_required
def nova_pergunta():
    form = QuestionForm()
    form.categorias.choices = [(c.id, c.name) for c in Category.query.all()]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.all()]

    if form.validate_on_submit():
        categorias = Category.query.filter(Category.id.in_(form.categorias.data)).all()
        tags = Tag.query.filter(Tag.id.in_(form.tags.data)).all()
        pergunta = Question(titulo=form.titulo.data, conteudo=form.conteudo.data, autor=current_user,
                            categorias=categorias, tags=tags)
        db.session.add(pergunta)
        db.session.commit()
        return redirect(url_for('dashboard', user_id=current_user.id))

    return render_template('nova_pergunta.html', form=form)

@app.route('/nova_resposta', methods=['GET', 'POST'])
@login_required
def nova_resposta():
    if request.method == 'POST':
        content = request.form['content']
        question_id = request.form['question_id']
        user_id = current_user.id

        new_answer = Answer(content=content, question_id=question_id, user_id=user_id)
        try:
            db.session.add(new_answer)
            db.session.commit()
            return redirect(url_for('dashboard', user_id=user_id))
        except Exception as e:
            return f'Error creating answer: {e}'
    question_id = request.args.get('question_id')
    user_id = current_user.id
    return render_template('nova_resposta.html', question_id=question_id, user_id=user_id)

@app.route('/search')
def search():
    query = request.args.get('query')
    results = Question.query.filter(Question.titulo.contains(query)).all()
    return render_template('search_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
