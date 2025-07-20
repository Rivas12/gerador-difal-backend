from flask import request, jsonify
from app.models import db, CertificadoDigital, NFexportdas, GnreGuia
from cryptography.hazmat.primitives.serialization import pkcs12
import os
import requests_pkcs12

def processar_upload_certificado(payload):
    """Processa o upload de certificado digital"""
    file = request.files.get('certificado')
    senha = request.form.get('senha')
    if not file or not senha:
        return jsonify({'erro': 'Arquivo e senha são obrigatórios'}), 400

    filename = file.filename
    if not (filename.lower().endswith('.pfx') or filename.lower().endswith('.p12')):
        return jsonify({'erro': 'Apenas arquivos .pfx ou .p12 são permitidos'}), 400

    upload_folder = os.environ.get('UPLOAD_FOLDER', './certs')
    os.makedirs(upload_folder, exist_ok=True)

    ext = os.path.splitext(filename)[1]
    new_filename = f"{payload['user_id']}{ext}"
    path = os.path.join(upload_folder, new_filename)
    file.save(path)

    # Validação da senha do certificado usando cryptography
    try:
        with open(path, "rb") as f:
            pfx_data = f.read()
        pkcs12.load_key_and_certificates(pfx_data, senha.encode())
    except Exception as e:
        os.remove(path)
        return jsonify({'erro': 'Senha do certificado inválida'}), 400

    try:
        CertificadoDigital.query.filter_by(user_id=payload['user_id']).delete()
        cert = CertificadoDigital(
            user_id=payload['user_id'],
            nome_arquivo=new_filename,
        )
        cert.senha = senha  
        db.session.add(cert)
        db.session.commit()
        return jsonify({'mensagem': 'Certificado salvo com sucesso', 'status': 'ok'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': 'Erro ao salvar certificado!', 'status': 'error'}), 500

def processar_criar_gnre(payload):
    """Processa a criação de GNRE"""
    try:
        user_id = payload['user_id']
        senha_certificado = "senha123"  # <-- Definindo a senha fixa aqui
        notas = db.session.query(NFexportdas).filter_by(user_id=user_id, status='pendente').all()
        if not notas:
            return jsonify({'erro': 'Nenhuma nota fiscal pendente encontrada'}), 404

        upload_folder = os.environ.get('UPLOAD_FOLDER', './certs')
        cert_path = os.path.join(upload_folder, f"{user_id}.pfx")
        if not os.path.exists(cert_path):
            cert_path = os.path.join(upload_folder, f"{user_id}.p12")
            if not os.path.exists(cert_path):
                return jsonify({'erro': 'Certificado digital não encontrado'}), 404

        # limites do GNRE
        MAX_LOTE_KB = 300
        MAX_GUIAS = 200

        # Construir lote de até MAX_GUIAS
        notas_lote = notas[:MAX_GUIAS]
        # verificar XML size após serializar
        # ... aqui geraria XML para checar tamanho em KB

        url_gnre = "https://www.testegnre.pe.gov.br/gnreWS/services/GnreLoteRecepcao"  # Produção
        resultados = []

        for nota in notas_lote:
            payload_gnre = {
                "ufFavorecida": nota.uf_favorecida,
                "codigoReceita": nota.codigo_receita,
                "valorPrincipal": str(nota.valor_total_nota),
                "cnpjEmitente": nota.cnpj_emitente,
                "razaoSocialEmitente": nota.razao_social_emitente,
                "periodoReferencia": f"{nota.ano_referencia}-{str(nota.mes_referencia).zfill(2)}",
                "chaveNfe": nota.chave_nfe
            }
            try:
                response = requests_pkcs12.post(
                    url_gnre,
                    json=payload_gnre,
                    pkcs12_filename=cert_path,
                    pkcs12_password=senha_certificado,
                    timeout=30,
                    verify=False
                )
                if response.status_code == 200:
                    resp_json = response.json()
                    guia = GnreGuia(
                        chave_nfe=nota.chave_nfe,
                        user_id=user_id,
                        valor_total=nota.valor_total_nota,
                        numero_guia=resp_json.get('numeroGuia'),
                        uf_favorecida=nota.uf_favorecida,
                        codigo_receita=nota.codigo_receita,
                        situacao=resp_json.get('situacao', 'gerado'),
                        linha_digitavel=resp_json.get('linhaDigitavel'),
                        url_pdf=resp_json.get('urlPdf')
                    )
                    db.session.add(guia)
                    nota.status = 'gerado'
                    resultados.append({'chave_nfe': nota.chave_nfe, 'status': 'ok', 'guia': resp_json})
                else:
                    resultados.append({'chave_nfe': nota.chave_nfe, 'status': 'erro', 'erro': response.text})
            except Exception as e:
                resultados.append({'chave_nfe': nota.chave_nfe, 'status': 'erro', 'erro': str(e)})

        db.session.commit()
        return jsonify({'resultados': resultados}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao criar GNRE: {str(e)}'}), 500
