from flask import Blueprint, request, jsonify
from app.auth.jwt_utils import decodeToken, login, cadastrar_usuario
from app.models import db, NFexportdas
import os
from datetime import timedelta, datetime
from sqlalchemy import text  # Adicione este import
import xml.etree.ElementTree as ET
from app.services.xml_reader import ler_xmls_util
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

@routes.route('/upload-certificado', methods=['POST'])
@token_required
def upload_certificado(payload):
    file = request.files.get('certificado')
    if not file:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    # Verifica extensão
    filename = file.filename
    if not (filename.lower().endswith('.pfx') or filename.lower().endswith('.p12')):
        return jsonify({'erro': 'Apenas arquivos .pfx ou .p12 são permitidos'}), 400

    upload_folder = os.environ.get('UPLOAD_FOLDER', './certs')
    os.makedirs(upload_folder, exist_ok=True)

    # Renomeia o arquivo com o user_id
    ext = os.path.splitext(filename)[1]
    new_filename = f"{payload['user_id']}{ext}"
    path = os.path.join(upload_folder, new_filename)
    file.save(path)
    return jsonify({'mensagem': 'Certificado salvo com sucesso', 'status': 'ok'})


@routes.route('/login-seguro', methods=['POST'])
def login_seguro():
    return login()

@routes.route('/ping', methods=['GET'])
@token_required
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

@routes.route('/listar-nfes', methods=['GET'])
@token_required
def listar_nfes(payload):
    try:
        nfes = db.session.query(NFexportdas).filter_by(user_id=payload['user_id']).all()
        nfes_list = []
        for nfe in nfes:
            nfes_list.append({
                'chave_nfe': nfe.chave_nfe,
                'numero_nf': nfe.numero_nota,
                'data_emissao': nfe.data_emissao_nota.strftime('%Y-%m-%d') if nfe.data_emissao_nota else None,
                'uf_favorecida': nfe.uf_favorecida,
                'valor_total_nota': str(nfe.valor_total_nota) if nfe.valor_total_nota else None,
                'razao_social_emitente': nfe.razao_social_emitente,
                'cnpj_emitente': nfe.cnpj_emitente,
                'natureza_receita': nfe.natureza_receita,
                'tipo_operacao': nfe.tipo_operacao
            })
        return jsonify({'nfes': nfes_list}), 200
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar NFes: {str(e)}'}), 500

@routes.route('/guardar_nfes', methods=['POST'])
@token_required
def guardar_nfes(payload):
    try:
        if 'archives' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

        arquivos = request.files.getlist('archives')
        arquivos_lidos = ler_xmls_util(arquivos)

        # Coletar todas as chaves das NFes recebidas
        chaves_arquivos = [dados.get('chave_acesso') for dados in arquivos_lidos if 'erro' not in dados]

        # Buscar todas as chaves já existentes no banco de uma vez
        chaves_existentes = set(
            x[0] for x in db.session.query(NFexportdas.chave_nfe)
            .filter(NFexportdas.chave_nfe.in_(chaves_arquivos)).all()
        )

        nfes_salvas = []
        nfes_ja_salvas = []
        erros = []
        for dados in arquivos_lidos:
            if 'erro' in dados:
                erros.append(dados)
                continue

            chave_nfe = dados.get('chave_acesso')
            if chave_nfe in chaves_existentes:
                nfes_ja_salvas.append({
                    'chave_nfe': chave_nfe,
                    'numero_nf': dados.get('numero_nf'),
                    'destinatario': dados.get('razao_destinatario')
                })
                continue

            try:
                data_emissao_nota = None
                if dados.get('data_emissao'):
                    try:
                        data_emissao_nota = datetime.strptime(dados['data_emissao'][:10], "%Y-%m-%d").date()
                    except Exception:
                        data_emissao_nota = None

                mes_referencia = None
                ano_referencia = None
                if data_emissao_nota:
                    mes_referencia = data_emissao_nota.month
                    ano_referencia = data_emissao_nota.year

                nfe = NFexportdas(
                    user_id=payload['user_id'],
                    uf_favorecida=dados.get('uf_destino'),
                    codigo_receita="100099",
                    valor_total_nota=dados.get('valor_total_nf'),
                    mes_referencia=mes_referencia,
                    ano_referencia=ano_referencia,
                    cnpj_emitente=dados.get('cnpj_emitente'),
                    razao_social_emitente=dados.get('razao_emitente'),
                    inscricao_estadual=dados.get('ie_emitente'),
                    uf_origem=dados.get('uf_origem'),
                    municipio_emitente_ibge=dados.get('codigo_municipio_origem'),
                    cep_emitente=dados.get('cep_emitente'),
                    endereco_emitente=dados.get('logradouro_emitente'),
                    numero_nota=dados.get('numero_nf'),
                    chave_nfe=chave_nfe,
                    data_emissao_nota=data_emissao_nota,
                    descricao_produto=dados.get('produto_predominante'),
                    natureza_receita=dados.get('natureza_receita', 'venda'),
                    tipo_operacao=dados.get('tipo_operacao', 'venda'),
                    codigo_municipio_destino=dados.get('codigo_municipio_destino'),
                    inscricao_estadual_destinatario=dados.get('ie_destinatario'),
                    icms_tipo=dados.get('icms_tipo'),
                    icms_base=dados.get('icms_base'),
                    icms_aliquota=dados.get('icms_aliquota'),
                    icms_valor=dados.get('icms_valor')
                )
                db.session.add(nfe)
                db.session.commit()  # Commit individual aqui
                nfes_salvas.append({
                    'chave_nfe': chave_nfe,
                    'numero_nf': dados.get('numero_nf'),
                    'destinatario': dados.get('razao_destinatario')
                })
            except Exception as e:
                db.session.rollback()
                erros.append({
                    'chave_nfe': chave_nfe,
                    'numero_nf': dados.get('numero_nf'),
                    'destinatario': dados.get('razao_destinatario'),
                    'erro': str(e),
                })

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'erro': f'Erro ao salvar no banco: {str(e)}',
                'exported': nfes_salvas,
                'already_saved': nfes_ja_salvas,
                'errors': erros
            }), 500

        return jsonify({
            'success': len(erros) == 0,
            'mensagem': f'{len(nfes_salvas)} NFes guardadas com sucesso, {len(erros)} com erro, {len(nfes_ja_salvas)} já existiam',
            'exported': nfes_salvas,
            'already_saved': nfes_ja_salvas,
            'errors': erros
        }), 200 if len(erros) == 0 else 207
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'erro': f'Erro ao guardar NFes: {str(e)}'}), 500
    
@routes.route('/cadastrar-usuario', methods=['POST'])
def cadastrar_user():
    return cadastrar_usuario()




