from flask import Blueprint, request, jsonify
from app.auth.jwt_utils import createAccessToken, decodeToken
from app.models import db
import os
from datetime import timedelta
from sqlalchemy import text  # Adicione este import
import xml.etree.ElementTree as ET

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
    arquivos_lidos = []

    # Define o namespace da NFe
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

    for arquivo in arquivos:
        if arquivo.filename.lower().endswith('.xml'):
            conteudo = arquivo.read().decode('utf-8')
            try:
                root = ET.fromstring(conteudo)

                # Dados principais
                nNF = root.find('.//nfe:infNFe/nfe:ide/nfe:nNF', ns)
                chNFe = root.find('.//nfe:protNFe/nfe:infProt/nfe:chNFe', ns)
                uf_origem = root.find('.//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:UF', ns)
                uf_destino = root.find('.//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:UF', ns)
                cnpj_emit = root.find('.//nfe:infNFe/nfe:emit/nfe:CNPJ', ns)
                cnpj_dest = root.find('.//nfe:infNFe/nfe:dest/nfe:CNPJ', ns)
                cpf_dest = root.find('.//nfe:infNFe/nfe:dest/nfe:CPF', ns)
                vNF = root.find('.//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vNF', ns)
                cfop = root.find('.//nfe:infNFe/nfe:det/nfe:prod/nfe:CFOP', ns)
                dhEmi = root.find('.//nfe:infNFe/nfe:ide/nfe:dhEmi', ns)
                cMun_origem = root.find('.//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:cMun', ns)
                cMun_destino = root.find('.//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:cMun', ns)

                # Emitente
                razao_emit = root.find('.//nfe:infNFe/nfe:emit/nfe:xNome', ns)
                ie_emit = root.find('.//nfe:infNFe/nfe:emit/nfe:IE', ns)
                fone_emit = root.find('.//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:fone', ns)
                ender_emit = root.find('.//nfe:infNFe/nfe:emit/nfe:enderEmit', ns)
                emit_logradouro = ender_emit.find('nfe:xLgr', ns) if ender_emit is not None else None
                emit_numero = ender_emit.find('nfe:nro', ns) if ender_emit is not None else None
                emit_bairro = ender_emit.find('nfe:bairro', ns) if ender_emit is not None else None
                emit_cep = ender_emit.find('nfe:CEP', ns) if ender_emit is not None else None
                emit_municipio = ender_emit.find('nfe:xMun', ns) if ender_emit is not None else None

                # Destinatário
                razao_dest = root.find('.//nfe:infNFe/nfe:dest/nfe:xNome', ns)
                ie_dest = root.find('.//nfe:infNFe/nfe:dest/nfe:IE', ns)
                ender_dest = root.find('.//nfe:infNFe/nfe:dest/nfe:enderDest', ns)
                dest_logradouro = ender_dest.find('nfe:xLgr', ns) if ender_dest is not None else None
                dest_numero = ender_dest.find('nfe:nro', ns) if ender_dest is not None else None
                dest_bairro = ender_dest.find('nfe:bairro', ns) if ender_dest is not None else None
                dest_cep = ender_dest.find('nfe:CEP', ns) if ender_dest is not None else None
                dest_municipio = ender_dest.find('nfe:xMun', ns) if ender_dest is not None else None

                # Produto predominante (primeiro item)
                prod_pred = root.find('.//nfe:infNFe/nfe:det/nfe:prod/nfe:xProd', ns)

                # Placa do veículo (se houver)
                placa_veic = root.find('.//nfe:infNFe/nfe:transp/nfe:veicTransp/nfe:placa', ns)

                # Data de vencimento (se houver)
                dt_venc = root.find('.//nfe:infNFe/nfe:cobr/nfe:dup/nfe:dVenc', ns)

                # ICMS (primeiro item)
                icms = root.find('.//nfe:infNFe/nfe:det/nfe:imposto/nfe:ICMS', ns)
                vICMS = None
                vBC = None
                pICMS = None
                vICMSUFDest = None
                if icms is not None:
                    # ICMS00, ICMS10, ICMS20, etc
                    for icms_tipo in icms:
                        vICMS = icms_tipo.find('nfe:vICMS', ns)
                        vBC = icms_tipo.find('nfe:vBC', ns)
                        pICMS = icms_tipo.find('nfe:pICMS', ns)
                        break  # só pega o primeiro grupo ICMS

                # ICMSUFDest (partilha interestadual)
                icms_ufdest = root.find('.//nfe:infNFe/nfe:det/nfe:imposto/nfe:ICMSUFDest', ns)
                if icms_ufdest is not None:
                    vICMSUFDest = icms_ufdest.find('nfe:vICMSUFDest', ns)

                arquivos_lidos.append({
                    'nome': arquivo.filename,
                    'numero_nf': nNF.text if nNF is not None else None,
                    'chave_acesso': chNFe.text if chNFe is not None else None,
                    'uf_origem': uf_origem.text if uf_origem is not None else None,
                    'uf_destino': uf_destino.text if uf_destino is not None else None,
                    'cnpj_emitente': cnpj_emit.text if cnpj_emit is not None else None,
                    'razao_emitente': razao_emit.text if razao_emit is not None else None,
                    'ie_emitente': ie_emit.text if ie_emit is not None else None,
                    'fone_emitente': fone_emit.text if fone_emit is not None else None,
                    'logradouro_emitente': emit_logradouro.text if emit_logradouro is not None else None,
                    'numero_emitente': emit_numero.text if emit_numero is not None else None,
                    'bairro_emitente': emit_bairro.text if emit_bairro is not None else None,
                    'cep_emitente': emit_cep.text if emit_cep is not None else None,
                    'municipio_emitente': emit_municipio.text if emit_municipio is not None else None,
                    'cnpj_destinatario': cnpj_dest.text if cnpj_dest is not None else (cpf_dest.text if cpf_dest is not None else None),
                    'razao_destinatario': razao_dest.text if razao_dest is not None else None,
                    'ie_destinatario': ie_dest.text if ie_dest is not None else None,
                    'logradouro_destinatario': dest_logradouro.text if dest_logradouro is not None else None,
                    'numero_destinatario': dest_numero.text if dest_numero is not None else None,
                    'bairro_destinatario': dest_bairro.text if dest_bairro is not None else None,
                    'cep_destinatario': dest_cep.text if dest_cep is not None else None,
                    'municipio_destinatario': dest_municipio.text if dest_municipio is not None else None,
                    'valor_total_nf': vNF.text if vNF is not None else None,
                    'cfop': cfop.text if cfop is not None else None,
                    'data_emissao': dhEmi.text if dhEmi is not None else None,
                    'codigo_municipio_origem': cMun_origem.text if cMun_origem is not None else None,
                    'codigo_municipio_destino': cMun_destino.text if cMun_destino is not None else None,
                    'produto_predominante': prod_pred.text if prod_pred is not None else None,
                    'placa_veiculo': placa_veic.text if placa_veic is not None else None,
                    'data_vencimento': dt_venc.text if dt_venc is not None else None,
                    'icms_valor': vICMS.text if vICMS is not None else None,
                    'icms_base_calculo': vBC.text if vBC is not None else None,
                    'icms_aliquota': pICMS.text if pICMS is not None else None,
                    'icms_ufdest': vICMSUFDest.text if vICMSUFDest is not None else None,
                })
            except Exception as e:
                arquivos_lidos.append({
                    'nome': arquivo.filename,
                    'erro': f'Erro ao ler XML: {str(e)}'
                })

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




