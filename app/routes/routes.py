from flask import Blueprint, request, jsonify
from app.auth.jwt_utils import decodeToken, login, cadastrar_usuario, atualizar_dados_usuario, obter_dados_usuario
from functools import wraps

routes = Blueprint('routes', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token and request.is_json:
            token = request.json.get('token')
        if not token:
            return jsonify({'erro': 'Token não fornecido'}), 401

        payload = decodeToken(token)
        if not payload:
            return jsonify({'erro': 'Token inválido ou expirado'}), 401

        # Passa o payload como argumento para a função decorada
        return f(payload, *args, **kwargs)
    return decorated

# =============================================================================
# ROTAS DE AUTENTICAÇÃO E USUÁRIOS
# =============================================================================

@routes.route('/login-seguro', methods=['POST'])
def login_seguro():
    """Rota para login seguro do usuário"""
    return login()

@routes.route('/cadastrar-usuario', methods=['POST'])
def cadastrar_user():
    """Rota para cadastrar novo usuário"""
    return cadastrar_usuario()

@routes.route('/atualizar-dados-usuario', methods=['PUT'])
def atualizar_dados_user():
    """Rota para atualizar dados do usuário"""
    return atualizar_dados_usuario()

@routes.route('/obter-dados-usuario', methods=['POST'])
def obter_dados_user():
    """Rota para obter dados do usuário"""
    return obter_dados_usuario()

# =============================================================================
# ROTAS DE CERTIFICADOS DIGITAIS
# =============================================================================

@routes.route('/upload-certificado', methods=['POST'])
@token_required
def upload_certificado(payload):
    """Rota para upload de certificado digital (.pfx/.p12)"""
    from app.services.certificado_service import processar_upload_certificado
    return processar_upload_certificado(payload)

# =============================================================================
# ROTAS DE XML E NOTAS FISCAIS
# =============================================================================

@routes.route('/ler-xmls', methods=['POST'])
def ler_xmls():
    """Rota para leitura e processamento de arquivos XML de NFe"""
    from app.services.xml_reader import processar_upload_xmls
    return processar_upload_xmls()

@routes.route('/listar-nfes', methods=['GET'])
@token_required
def listar_nfes(payload):
    """Rota para listar todas as NFes do usuário"""
    from app.services.nfe_service import listar_nfes_usuario
    return listar_nfes_usuario(payload)

@routes.route('/guardar_nfes', methods=['POST'])
@token_required
def guardar_nfes(payload):
    """Rota para guardar NFes processadas no banco de dados"""
    from app.services.nfe_service import guardar_nfes_usuario
    return guardar_nfes_usuario(payload)

# =============================================================================
# ROTAS DE GNRE (GUIA NACIONAL DE RECOLHIMENTO ESTADUAL)
# =============================================================================

@routes.route('/criar-gnre', methods=['POST'])
@token_required
def criar_gnre(payload):
    """Rota para criação de GNRE baseado nas NFes pendentes"""
    from app.services.certificado_service import processar_criar_gnre
    return processar_criar_gnre(payload)

@routes.route('/listar-guias', methods=['GET'])
@token_required
def listar_guias(payload):
    """Rota para listar todas as guias GNRE do usuário com dados da NFe"""
    from app.services.gnre_service import listar_guias_usuario
    return listar_guias_usuario(payload)

@routes.route('/obter-guia/<int:guia_id>', methods=['GET'])
@token_required
def obter_guia(payload, guia_id):
    """Rota para obter uma guia GNRE específica com dados completos da NFe"""
    from app.services.gnre_service import obter_guia_por_id
    return obter_guia_por_id(payload, guia_id)

# =============================================================================
# ROTAS DE DASHBOARD E SISTEMA
# =============================================================================

@routes.route('/ping', methods=['GET'])
@token_required
def ping():
    """Rota para verificar status da API e conectividade com banco de dados"""
    from app.services.dashboard_service import verificar_status_api
    return verificar_status_api()

@routes.route('/dashboard', methods=['GET'])
@token_required
def dashboard(payload):
    """Rota para obter dados do dashboard do usuário"""
    from app.services.dashboard_service import obter_dashboard_usuario
    return obter_dashboard_usuario(payload)