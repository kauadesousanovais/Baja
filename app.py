from flask import Flask, send_from_directory, render_template, request, redirect, url_for
import os
import json
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime


import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key-development")

database_url = os.getenv("DATABASE_URL", 'sqlite:///site.db')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ==========================
# MODELOS
# ==========================

class Parceiro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(200), nullable=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imagem_url = db.Column(db.String(200), nullable=False)
    link_post = db.Column(db.String(300), nullable=False)
    legenda = db.Column(db.String(200), nullable=True)


# ==========================
# FUNÇÃO GOOGLE SHEETS
# ==========================

def salvar_no_sheets(nome, matricula, curso, subsistema, carta):

    creds_json = os.getenv("GOOGLE_CREDENTIALS")

    if not creds_json:
        print("Credenciais do Google não configuradas.")
        return

    creds_dict = json.loads(creds_json)

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    sheet = client.open("Processo Seletivo Iaguary").sheet1

    sheet.append_row([
        nome,
        matricula,
        curso,
        subsistema,
        carta,
        datetime.now().strftime("%d/%m/%Y %H:%M")
    ])


# ==========================
# ROTAS
# ==========================

@app.route('/')
def index():

    try:
        todos_parceiros = Parceiro.query.all()
    except Exception as e:
        print(f"Erro ao buscar parceiros: {e}")
        todos_parceiros = []

    parceiros_com_imagem = [p for p in todos_parceiros if p.logo]

    try:
        posts = Post.query.all()
    except Exception as e:
        print(f"Erro ao buscar posts: {e}")
        posts = []

    return render_template('index.html',
                           lista_parceiros=parceiros_com_imagem,
                           lista_posts=posts)


@app.route('/processo-seletivo')
def processo_seletivo():
    return render_template('processo_seletivo.html')


@app.route('/enviar-inscricao', methods=['POST'])
def enviar_inscricao():

    nome = request.form.get('nome')
    matricula = request.form.get('matricula')
    curso = request.form.get('curso')
    subsistema = request.form.get('subsistema')
    carta = request.form.get('carta')

    if not all([nome, matricula, curso, subsistema, carta]):
        return "Erro: todos os campos são obrigatórios.", 400

    salvar_no_sheets(nome, matricula, curso, subsistema, carta)

    return redirect(url_for('processo_seletivo'))


# ==========================
# EXECUÇÃO LOCAL
# ==========================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Tabelas verificadas/criadas.")

    app.run(debug=True, port=5000)