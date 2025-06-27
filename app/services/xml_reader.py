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

def processar_xml(nome_arquivo, conteudo, ns):
    try:
        root = ET.fromstring(conteudo)
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
        razao_emit = root.find('.//nfe:infNFe/nfe:emit/nfe:xNome', ns)
        ie_emit = root.find('.//nfe:infNFe/nfe:emit/nfe:IE', ns)
        fone_emit = root.find('.//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:fone', ns)
        ender_emit = root.find('.//nfe:infNFe/nfe:emit/nfe:enderEmit', ns)
        emit_logradouro = ender_emit.find('nfe:xLgr', ns) if ender_emit is not None else None
        emit_numero = ender_emit.find('nfe:nro', ns) if ender_emit is not None else None
        emit_bairro = ender_emit.find('nfe:bairro', ns) if ender_emit is not None else None
        emit_cep = ender_emit.find('nfe:CEP', ns) if ender_emit is not None else None
        emit_municipio = ender_emit.find('nfe:xMun', ns) if ender_emit is not None else None
        razao_dest = root.find('.//nfe:infNFe/nfe:dest/nfe:xNome', ns)
        ie_dest = root.find('.//nfe:infNFe/nfe:dest/nfe:IE', ns)
        ender_dest = root.find('.//nfe:infNFe/nfe:dest/nfe:enderDest', ns)
        dest_logradouro = ender_dest.find('nfe:xLgr', ns) if ender_dest is not None else None
        dest_numero = ender_dest.find('nfe:nro', ns) if ender_dest is not None else None
        dest_bairro = ender_dest.find('nfe:bairro', ns) if ender_dest is not None else None
        dest_cep = ender_dest.find('nfe:CEP', ns) if ender_dest is not None else None
        dest_municipio = ender_dest.find('nfe:xMun', ns) if ender_dest is not None else None
        prod_pred = root.find('.//nfe:infNFe/nfe:det/nfe:prod/nfe:xProd', ns)
        placa_veic = root.find('.//nfe:infNFe/nfe:transp/nfe:veicTransp/nfe:placa', ns)
        dt_venc = root.find('.//nfe:infNFe/nfe:cobr/nfe:dup/nfe:dVenc', ns)
        icms = root.find('.//nfe:infNFe/nfe:det/nfe:imposto/nfe:ICMS', ns)
        vICMS = None
        vBC = None
        pICMS = None
        vICMSUFDest = None
        if icms is not None:
            for icms_tipo in icms:
                vICMS = icms_tipo.find('nfe:vICMS', ns)
                vBC = icms_tipo.find('nfe:vBC', ns)
                pICMS = icms_tipo.find('nfe:pICMS', ns)
                break
        icms_ufdest = root.find('.//nfe:infNFe/nfe:det/nfe:imposto/nfe:ICMSUFDest', ns)
        if icms_ufdest is not None:
            vICMSUFDest = icms_ufdest.find('nfe:vICMSUFDest', ns)
        return [{
            'nome': nome_arquivo,
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
        }]
    except Exception as e:
        return [{
            'nome': nome_arquivo,
            'erro': f'Erro ao ler XML: {str(e)}'
        }]
