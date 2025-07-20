import xml.etree.ElementTree as ET
from flask import request
import zipfile
import io
import rarfile  # Adicione esta linha

def ler_xmls_util(arquivos):
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    arquivos_lidos = []
    for arquivo in arquivos:
        if arquivo.filename.lower().endswith('.xml'):
            conteudo = arquivo.read().decode('utf-8')
            arquivos_lidos.extend(processar_xml(arquivo.filename, conteudo, ns))
        elif arquivo.filename.lower().endswith('.zip'):
            zip_bytes = arquivo.read()
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                for nome_arquivo in z.namelist():
                    if nome_arquivo.lower().endswith('.xml'):
                        conteudo = z.read(nome_arquivo).decode('utf-8')
                        arquivos_lidos.extend(processar_xml(nome_arquivo, conteudo, ns))
        elif arquivo.filename.lower().endswith('.rar'):
            rar_bytes = arquivo.read()
            with rarfile.RarFile(io.BytesIO(rar_bytes)) as r:
                for info in r.infolist():
                    if info.filename.lower().endswith('.xml'):
                        conteudo = r.read(info).decode('utf-8')
                        arquivos_lidos.extend(processar_xml(info.filename, conteudo, ns))
    return arquivos_lidos

def get_text(element, path, ns):
    el = element.find(path, ns)
    return el.text if el is not None and el.text is not None else ''

def processar_xml(nome_arquivo, conteudo, ns):
    try:
        root = ET.fromstring(conteudo)
        nNF = get_text(root, './/nfe:infNFe/nfe:ide/nfe:nNF', ns)
        chNFe = get_text(root, './/nfe:protNFe/nfe:infProt/nfe:chNFe', ns)
        uf_origem = get_text(root, './/nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:UF', ns)
        uf_destino = get_text(root, './/nfe:infNFe/nfe:dest/nfe:enderDest/nfe:UF', ns)
        cnpj_emit = get_text(root, './/nfe:infNFe/nfe:emit/nfe:CNPJ', ns)
        cnpj_dest = get_text(root, './/nfe:infNFe/nfe:dest/nfe:CNPJ', ns)
        cpf_dest = get_text(root, './/nfe:infNFe/nfe:dest/nfe:CPF', ns)
        vNF = get_text(root, './/nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vNF', ns)
        cfop = get_text(root, './/nfe:infNFe/nfe:det/nfe:prod/nfe:CFOP', ns)
        dhEmi = get_text(root, './/nfe:infNFe/nfe:ide/nfe:dhEmi', ns)
        cMun_origem = get_text(root, './/nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:cMun', ns)
        cMun_destino = get_text(root, './/nfe:infNFe/nfe:dest/nfe:enderDest/nfe:cMun', ns)
        razao_emit = get_text(root, './/nfe:infNFe/nfe:emit/nfe:xNome', ns)
        ie_emit = get_text(root, './/nfe:infNFe/nfe:emit/nfe:IE', ns)
        fone_emit = get_text(root, './/nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:fone', ns)
        ender_emit = root.find('.//nfe:infNFe/nfe:emit/nfe:enderEmit', ns)
        emit_logradouro = get_text(ender_emit, 'nfe:xLgr', ns) if ender_emit is not None else ''
        emit_numero = get_text(ender_emit, 'nfe:nro', ns) if ender_emit is not None else ''
        emit_bairro = get_text(ender_emit, 'nfe:bairro', ns) if ender_emit is not None else ''
        emit_cep = get_text(ender_emit, 'nfe:CEP', ns) if ender_emit is not None else ''
        emit_municipio = get_text(ender_emit, 'nfe:xMun', ns) if ender_emit is not None else ''
        razao_dest = get_text(root, './/nfe:infNFe/nfe:dest/nfe:xNome', ns)
        ie_dest = get_text(root, './/nfe:infNFe/nfe:dest/nfe:IE', ns)
        ender_dest = root.find('.//nfe:infNFe/nfe:dest/nfe:enderDest', ns)
        dest_logradouro = get_text(ender_dest, 'nfe:xLgr', ns) if ender_dest is not None else ''
        dest_numero = get_text(ender_dest, 'nfe:nro', ns) if ender_dest is not None else ''
        dest_bairro = get_text(ender_dest, 'nfe:bairro', ns) if ender_dest is not None else ''
        dest_cep = get_text(ender_dest, 'nfe:CEP', ns) if ender_dest is not None else ''
        dest_municipio = get_text(ender_dest, 'nfe:xMun', ns) if ender_dest is not None else ''
        prod_pred = get_text(root, './/nfe:infNFe/nfe:det/nfe:prod/nfe:xProd', ns)
        placa_veic = get_text(root, './/nfe:infNFe/nfe:transp/nfe:veicTransp/nfe:placa', ns)
        dt_venc = get_text(root, './/nfe:infNFe/nfe:cobr/nfe:dup/nfe:dVenc', ns)
        icms = root.find('.//nfe:infNFe/nfe:det/nfe:imposto/nfe:ICMS', ns)
        tipo_op = get_text(root, './/nfe:infNFe/nfe:ide/nfe:tpNF', ns)
        natureza_receita = get_text(root, './/nfe:infNFe/nfe:ide/nfe:natOp', ns)
        vICMS = ''
        vBC = ''
        pICMS = ''
        if icms is not None:
            for icms_tipo in icms:
                vICMS = get_text(icms_tipo, 'nfe:vICMS', ns)
                vBC = get_text(icms_tipo, 'nfe:vBC', ns)
                pICMS = get_text(icms_tipo, 'nfe:pICMS', ns)
                break
        # Dados do DIFAL (ICMSUFDest)
        icms_ufdest = root.find('.//nfe:infNFe/nfe:det/nfe:imposto/nfe:ICMSUFDest', ns)
        vICMSUFDest = get_text(icms_ufdest, 'nfe:vICMSUFDest', ns) if icms_ufdest is not None else ''
        vICMSUFRemet = get_text(icms_ufdest, 'nfe:vICMSUFRemet', ns) if icms_ufdest is not None else ''
        vBCUFDest = get_text(icms_ufdest, 'nfe:vBCUFDest', ns) if icms_ufdest is not None else ''
        pICMSUFDest = get_text(icms_ufdest, 'nfe:pICMSUFDest', ns) if icms_ufdest is not None else ''
        pICMSInter = get_text(icms_ufdest, 'nfe:pICMSInter', ns) if icms_ufdest is not None else ''
        pICMSInterPart = get_text(icms_ufdest, 'nfe:pICMSInterPart', ns) if icms_ufdest is not None else ''
        
        return [{
            'nome': nome_arquivo or '',
            'numero_nf': nNF,
            'chave_acesso': chNFe,
            'uf_origem': uf_origem,
            'uf_destino': uf_destino,
            'cnpj_emitente': cnpj_emit,
            'razao_emitente': razao_emit,
            'ie_emitente': ie_emit,
            'fone_emitente': fone_emit,
            'logradouro_emitente': emit_logradouro,
            'numero_emitente': emit_numero,
            'bairro_emitente': emit_bairro,
            'cep_emitente': emit_cep,
            'municipio_emitente': emit_municipio,
            'cnpj_destinatario': cnpj_dest if cnpj_dest else cpf_dest,
            'razao_destinatario': razao_dest,
            'ie_destinatario': ie_dest,
            'logradouro_destinatario': dest_logradouro,
            'numero_destinatario': dest_numero,
            'bairro_destinatario': dest_bairro,
            'cep_destinatario': dest_cep,
            'municipio_destinatario': dest_municipio,
            'valor_total_nf': vNF,
            'cfop': cfop,
            'data_emissao': dhEmi,
            'codigo_municipio_origem': cMun_origem,
            'codigo_municipio_destino': cMun_destino,
            'produto_predominante': prod_pred,
            'placa_veiculo': placa_veic,
            'data_vencimento': dt_venc,
            'icms_tipo': icms_tipo.tag.split('}')[-1] if icms is not None and len(icms) > 0 else '',
            'icms_base': vBC,
            'icms_aliquota': pICMS,
            'icms_valor': vICMS,
            # Dados do DIFAL
            'difal_valor_destino': vICMSUFDest,  # Valor do ICMS devido à UF de destino
            'difal_valor_remetente': vICMSUFRemet,  # Valor do ICMS devido à UF do remetente
            'difal_base_calculo': vBCUFDest,  # Base de cálculo do DIFAL
            'difal_aliquota_destino': pICMSUFDest,  # Alíquota do ICMS da UF de destino
            'difal_aliquota_interestadual': pICMSInter,  # Alíquota interestadual
            'difal_percentual_partilha': pICMSInterPart,  # Percentual de partilha
            'tipo_operacao': tipo_op,
            'natureza_receita': natureza_receita,
        }]
    except Exception as e:
        return [{
            'nome': nome_arquivo or '',
            'erro': f'Erro ao ler XML: {str(e)}'
        }]

def processar_upload_xmls():
    from flask import request, jsonify
    
    if 'archives' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    arquivos = request.files.getlist('archives')
    arquivos_lidos = ler_xmls_util(arquivos)
    return jsonify({'xmls': arquivos_lidos}), 200
