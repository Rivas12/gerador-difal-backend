from flask import Blueprint, request, jsonify
from app.auth.jwt_utils import createAccessToken, decodeToken
from app.models import db
import os
from datetime import timedelta

routes = Blueprint('routes', __name__)

@routes.route('/upload-certificado', methods=['POST'])
def upload_certificado():
    file = request.files.get('certificado')
    if not file:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    upload_folder = os.environ.get('UPLOAD_FOLDER', './uploads')
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, file.filename)
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
        db.session.execute('SELECT 1')
        db_status = 'ok'
    except Exception as e:
        db_status = f'erro: {str(e)}'
    return jsonify({
        'status': 'ok',
        'mensagem': 'API está funcionando',
        'db_status': db_status
    }), 200




