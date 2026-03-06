from flask import Flask, send_from_directory, render_template, request, redirect, url_for, flash
import os
import json
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from datetime import datetime
from zoneinfo import ZoneInfo

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import gspread
from google.oauth2.service_account import Credentials

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key-development")

database_url = os.getenv("DATABASE_URL", 'sqlite:///site.db')       

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# MODELOS

class Parceiro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(200), nullable=True)


#FUNÇÃO SALVAR CREDENCIAIS
def pegar_credenciais():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")

    if not creds_json:
        print("Credenciais do Google não configuradas.")
        return

    creds_dict = json.loads(creds_json)

    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]

    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )

    return credentials

# FUNÇÃO GOOGLE SHEETS

def salvar_no_sheets(credentials, nome, email, matricula, telefone, cpf, curso, semestre, subsistema, link_pdf):

    client = gspread.authorize(credentials)

    sheet = client.open_by_key("131Ja3xT9Q2IW85fBmkLT5jtctAvasHway0D6O0SKxBw").sheet1

    data = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

    sheet.append_row([
        nome,
        email,
        matricula,
        telefone,
        cpf,
        curso,
        semestre,
        subsistema,
        link_pdf,
        data
    ])

#FUNÇÃO ENVIAR PDF
def upload_pdf_drive(credentials, arquivo, nome):

    drive_service = build('drive', 'v3', credentials=credentials)

    pasta_id = "1Hke7-6_w4eZDme2MMXh0SOI3bNAhvujY"

    file_metadata = {
        'name': f'carta_{nome}.pdf',
        'parents': [pasta_id]
    }
    
    media = MediaIoBaseUpload(
        io.BytesIO(arquivo.read()),
        mimetype='application/pdf'
    )

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    drive_service.permissions().create(
    fileId=file.get("id"),
    body={"type": "anyone", "role": "reader"}
    ).execute()

    file_id = file.get('id')

    link = f"https://drive.google.com/file/d/{file_id}/view"

    return link

#FUNÇÃO EMAIL
def enviar_email_confirmacao(destinatario, nome):
    try:
        remetente = os.getenv("EMAIL_REMETENTE")
        senha = os.getenv("EMAIL_SENHA")

        msg = MIMEMultipart()
        msg["From"] = remetente
        msg["To"] = destinatario
        msg["Subject"] = "Confirmação de Inscrição - Processo Seletivo Iaguary"

        corpo = f"""
        Olá {nome},

        Sua inscrição no Processo Seletivo Iaguary foi recebida com sucesso!

        Em breve entraremos em contato com mais informações.

        Atenciosamente,
        Equipe Iaguary Baja
            """

        msg.attach(MIMEText(corpo, "plain"))

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(remetente, senha)
        servidor.send_message(msg)
        servidor.quit()

        print("Email enviado com sucesso.")

    except Exception as e:
        print("Erro ao enviar email:", e)

# ROTAS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/processo-seletivo')
def processo_seletivo():
    return render_template('processo_seletivo.html')


@app.route('/enviar-inscricao', methods=['POST'])
def enviar_inscricao():

    nome = request.form.get('nome')
    email = request.form.get('email')
    matricula = request.form.get('matricula')
    telefone = request.form.get('telefone')
    cpf = request.form.get('cpf')
    curso = request.form.get('curso')
    semestre = request.form.get('semestre')
    subsistema = request.form.get('subsistema')
    carta_pdf = request.files.get('carta_pdf')

    credentials = pegar_credenciais()

    link_pdf = upload_pdf_drive(credentials, carta_pdf, nome)

    sucesso = salvar_no_sheets(credentials, nome, email, matricula, telefone, cpf, curso, semestre, subsistema, link_pdf)

    if not sucesso:
        flash("Erro interno ao salvar inscrição.", "erro")
        return redirect(url_for('processo_seletivo'))

    enviar_email_confirmacao(email, nome)

    flash("Inscrição realizada com sucesso! Verifique seu email.", "sucesso")
    return redirect(url_for('processo_seletivo'))