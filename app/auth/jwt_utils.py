from datetime import datetime, timedelta, timezone
from app.models import db
from flask import jsonify, request
import jwt
import os
from dotenv import load_dotenv

from app.models import Usuario, UsuarioDados

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
            # Gerar novo token com data de expiração renovada
            new_token = createAccessToken(
                {
                    "user_id": payload.get("user_id"),
                    "email": payload.get("email"),
                    "role": payload.get("role", "admin"),
                    "username": payload.get("username")
                },
                expires_delta=timedelta(minutes=10)
            )
            return jsonify({
                'valido': True, 
                'mensagem': 'Token válido e renovado', 
                'token': new_token,
                **payload
            }), 200
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
            expires_delta=timedelta(minutes=10)
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
    
    # Dados complementares do usuário
    razao_social = data.get('razao_social')
    cnpj = data.get('cnpj')
    endereco = data.get('endereco')
    inscricao_estadual = data.get('inscricao_estadual')
    whatsapp = data.get('whatsapp')
    telefone = data.get('telefone')

    if not username or not email or not password:
        return jsonify({'success': False, 'erro': 'username, email e password são obrigatórios'}), 400

    from app.models import Usuario
    # Verifica se já existe usuário com mesmo email ou username
    if Usuario.query.filter((Usuario.email == email) | (Usuario.username == username)).first():
        return jsonify({'success': False, 'erro': 'Usuário já existe com este email ou username'}), 409

    # Verifica se CNPJ já existe (se fornecido)
    if cnpj:
        if UsuarioDados.query.filter_by(cnpj=cnpj).first():
            return jsonify({'success': False, 'erro': 'CNPJ já cadastrado no sistema'}), 409

    try:
        # Criar usuário
        usuario = Usuario(username=username, email=email)
        usuario.senha = password  # setter já faz hash
        db.session.add(usuario)
        db.session.flush()  # Para obter o ID do usuário

        # Criar dados complementares do usuário
        usuario_dados = UsuarioDados(
            user_id=usuario.id,
            razao_social=razao_social,
            cnpj=cnpj,
            endereco=endereco,
            inscricao_estadual=inscricao_estadual,
            whatsapp=whatsapp,
            telefone=telefone
        )
        db.session.add(usuario_dados)
        db.session.commit()

        # Gerar token para o novo usuário
        token = createAccessToken(
            {
                "user_id": usuario.id,
                "email": usuario.email,
                "role": "user",
                "username": usuario.username
            },
            expires_delta=timedelta(minutes=10)
        )

        return jsonify({
            'success': True, 
            'mensagem': 'Usuário cadastrado com sucesso', 
            'token': token,
            'usuario': {
                'id': usuario.id,
                'username': usuario.username,
                'email': usuario.email,
                'razao_social': razao_social,
                'cnpj': cnpj
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'erro': f'Erro ao cadastrar usuário: {str(e)}'}), 500


def atualizar_dados_usuario():
    """Atualiza os dados complementares do usuário"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'success': False, 'erro': 'Token é obrigatório'}), 401
    
    payload = decodeToken(token)
    if not payload:
        return jsonify({'success': False, 'erro': 'Token inválido ou expirado'}), 401
    
    user_id = payload.get('user_id')
    
    # Dados a serem atualizados
    razao_social = data.get('razao_social')
    cnpj = data.get('cnpj')
    endereco = data.get('endereco')
    inscricao_estadual = data.get('inscricao_estadual')
    whatsapp = data.get('whatsapp')
    telefone = data.get('telefone')
    
    try:
        # Busca os dados existentes do usuário
        usuario_dados = UsuarioDados.query.filter_by(user_id=user_id).first()
        
        if not usuario_dados:
            # Se não existir, cria um novo registro
            usuario_dados = UsuarioDados(user_id=user_id)
            db.session.add(usuario_dados)
        
        # Verifica se CNPJ já existe em outro usuário (se fornecido e mudou)
        if cnpj and cnpj != usuario_dados.cnpj:
            cnpj_existente = UsuarioDados.query.filter(
                UsuarioDados.cnpj == cnpj,
                UsuarioDados.user_id != user_id
            ).first()
            if cnpj_existente:
                return jsonify({'success': False, 'erro': 'CNPJ já cadastrado para outro usuário'}), 409
        
        # Atualiza os campos (apenas se fornecidos)
        if razao_social is not None:
            usuario_dados.razao_social = razao_social
        if cnpj is not None:
            usuario_dados.cnpj = cnpj
        if endereco is not None:
            usuario_dados.endereco = endereco
        if inscricao_estadual is not None:
            usuario_dados.inscricao_estadual = inscricao_estadual
        if whatsapp is not None:
            usuario_dados.whatsapp = whatsapp
        if telefone is not None:
            usuario_dados.telefone = telefone
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensagem': 'Dados atualizados com sucesso',
            'dados': {
                'razao_social': usuario_dados.razao_social,
                'cnpj': usuario_dados.cnpj,
                'endereco': usuario_dados.endereco,
                'inscricao_estadual': usuario_dados.inscricao_estadual,
                'whatsapp': usuario_dados.whatsapp,
                'telefone': usuario_dados.telefone
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'erro': f'Erro ao atualizar dados: {str(e)}'}), 500


def obter_dados_usuario():
    """Obtém os dados completos do usuário"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'success': False, 'erro': 'Token é obrigatório'}), 401
    
    payload = decodeToken(token)
    if not payload:
        return jsonify({'success': False, 'erro': 'Token inválido ou expirado'}), 401
    
    user_id = payload.get('user_id')
    
    try:
        from app.models import Usuario
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return jsonify({'success': False, 'erro': 'Usuário não encontrado'}), 404
        
        usuario_dados = UsuarioDados.query.filter_by(user_id=user_id).first()
        
        dados_resposta = {
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'data_created': usuario.data_created.isoformat() if usuario.data_created else None,
            'razao_social': usuario_dados.razao_social if usuario_dados else None,
            'cnpj': usuario_dados.cnpj if usuario_dados else None,
            'endereco': usuario_dados.endereco if usuario_dados else None,
            'inscricao_estadual': usuario_dados.inscricao_estadual if usuario_dados else None,
            'whatsapp': usuario_dados.whatsapp if usuario_dados else None,
            'telefone': usuario_dados.telefone if usuario_dados else None
        }
        
        return jsonify({
            'success': True,
            'dados': dados_resposta
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'erro': f'Erro ao obter dados: {str(e)}'}), 500