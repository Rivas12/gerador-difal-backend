from flask import Blueprint, request, jsonify
from app.auth.jwt_utils import createAccessToken, decodeToken
from app.models import db
import os
from datetime import timedelta
from sqlalchemy import text  # Adicione este import
import xml.etree.ElementTree as ET
from app.services.xml_reader import ler_xmls_util

routes = Blueprint('routes', __name__)

@routes.route('/upload-certificado', methods=['POST'])
def upload_certificado():
    file = request.files.get('certificado')
    if not file:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    # Verifica extensão
    filename = file.filename
    if not (filename.lower().endswith('.pfx') or filename.lower().endswith('.p12')):
        return jsonify({'erro': 'Apenas arquivos .pfx ou .p12 são permitidos'}), 400

    upload_folder = os.environ.get('UPLOAD_FOLDER', './certs')
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, filename)
    file.save(path)
    return jsonify({'mensagem': 'Certificado salvo com sucesso'})


@routes.route('/loginSeguro', methods=['POST'])
def login():
    data = request.get_json()
    token = data.get('token')
    if token:
        payload = decodeToken(token)
        if payload:
            return jsonify({'valido': True, 'mensagem': 'Token válido', **payload}), 200
        else:
            return jsonify({'valido': False,}), 401

    email = data.get('email')
    password = data.get('password')

    if email == 'admin' and password == 'senha123':
        token = createAccessToken(
            {
                "user_id": 1,
                "email": email,
                "role": "admin",
                "username": "Administrador"
            },
            expires_delta=timedelta(hours=24)
        )
        return jsonify({'token': token}), 200
    else:
        return jsonify({'erro': 'Credenciais inválidas'}), 401
    

@routes.route('/ping', methods=['GET'])
def ping():
    try:
        db.session.execute(text('SELECT 1'))  # Use text() aqui
        db_status = 'ok'
    except Exception as e:
        db_status = f'erro: {str(e)}'
    return jsonify({
        'api_status': 'ok',
        'mensagem': 'API está funcionando',
        'db_status': db_status
    }), 200

@routes.route('/ler-xmls', methods=['POST'])
def ler_xmls():
    if 'archives' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    arquivos = request.files.getlist('archives')
    arquivos_lidos = ler_xmls_util(arquivos)
    return jsonify({'xmls': arquivos_lidos}), 200

@routes.route('/cadastrar-usuario', methods=['POST'])
def cadastrar_usuario():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'success': False, 'erro': 'username, email e password são obrigatórios'}), 400

    from app.models import Usuario
    # Verifica se já existe usuário com mesmo email ou username
    if Usuario.query.filter((Usuario.email == email) | (Usuario.username == username)).first():
        return jsonify({'success': False, 'erro': 'Usuário já existe com este email ou username'}), 409

    try:
        usuario = Usuario(username=username, email=email)
        usuario.senha = password  # setter já faz hash
        db.session.add(usuario)
        db.session.commit()
        return jsonify({'success': True, 'mensagem': 'Usuário cadastrado com sucesso'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'erro': f'Erro ao cadastrar usuário: {str(e)}'}), 500




