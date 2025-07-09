from datetime import datetime, timedelta, timezone
from app.models import db
from flask import jsonify, request
import jwt
import os
from dotenv import load_dotenv

from app.models import Usuario

load_dotenv()

SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 200))

def createAccessToken(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decodeToken(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
def login():
    data = request.get_json()
    token = data.get('token')
    if token:
        payload = decodeToken(token)
        if payload:
            return jsonify({'valido': True, 'mensagem': 'Token válido', **payload}), 200
        else:
            return jsonify({'valido': False}), 401

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'erro': 'Email e senha são obrigatórios'}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario and usuario.verificar_senha(password):
        token = createAccessToken(
            {
                "user_id": usuario.id,
                "email": usuario.email,
                "role": getattr(usuario, 'role', 'admin'),
                "username": usuario.username
            },
            expires_delta=timedelta(hours=24)
        )
        payload = decodeToken(token)
        return jsonify({'valido': True, 'mensagem': 'Login realizado com sucesso', 'token': token, **payload}), 200
    else:
        return jsonify({'erro': 'Credenciais inválidas'}), 401
    

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

        # Gerar token para o novo usuário
        token = createAccessToken(
            {
                "user_id": usuario.id,
                "email": usuario.email,
                "role": "user",
                "username": usuario.username
            },
            expires_delta=timedelta(hours=24)
        )

        return jsonify({'success': True, 'mensagem': 'Usuário cadastrado com sucesso', 'token': token}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'erro': f'Erro ao cadastrar usuário: {str(e)}'}), 500