from flask import request, jsonify
from app.models import db, NFexportdas, AtividadesRecentes
from app.services.xml_reader import ler_xmls_util
from datetime import datetime

def listar_nfes_usuario(payload):
    """Lista todas as NFes de um usuário"""
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
                'razao_destinatario': nfe.razao_social_destinatario,
                'cnpj_emitente': nfe.cnpj_emitente,
                'cnpj_destinatario': nfe.cnpj_destinatario,
                'uf_destino': nfe.uf_destino,
                'endereco_destinatario': nfe.endereco_destinatario,
                'cep_destinatario': nfe.cep_destinatario,
                'municipio_destinatario_ibge': nfe.municipio_destinatario_ibge,
                'natureza_receita': nfe.natureza_receita,
                'tipo_operacao': nfe.tipo_operacao,
                # Dados do DIFAL
                'difal_valor_destino': str(nfe.difal_valor_destino) if nfe.difal_valor_destino else None,
                'difal_valor_remetente': str(nfe.difal_valor_remetente) if nfe.difal_valor_remetente else None,
                'difal_base_calculo': str(nfe.difal_base_calculo) if nfe.difal_base_calculo else None,
                'difal_aliquota_destino': str(nfe.difal_aliquota_destino) if nfe.difal_aliquota_destino else None,
                'difal_aliquota_interestadual': str(nfe.difal_aliquota_interestadual) if nfe.difal_aliquota_interestadual else None,
                'difal_percentual_partilha': str(nfe.difal_percentual_partilha) if nfe.difal_percentual_partilha else None
            })
        return jsonify(nfes_list), 200
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar NFes: {str(e)}'}), 500

def guardar_nfes_usuario(payload):
    """Processa e guarda NFes do usuário"""
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
            if not chave_nfe:
                erros.append({
                    'arquivo': dados.get('nome', 'arquivo desconhecido'),
                    'erro': 'Chave NFE não encontrada no XML'
                })
                continue
                
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
                else:
                    # Se não há data de emissão, usar mês/ano atual
                    hoje = datetime.now()
                    mes_referencia = hoje.month
                    ano_referencia = hoje.year

                nfe = NFexportdas(
                    user_id=payload['user_id'],
                    uf_favorecida=dados.get('uf_destino') or None,
                    codigo_receita="100099",
                    valor_total_nota=dados.get('valor_total_nf') or None,
                    mes_referencia=mes_referencia,
                    ano_referencia=ano_referencia,
                    cnpj_emitente=dados.get('cnpj_emitente') or None,
                    razao_social_emitente=dados.get('razao_emitente') or None,
                    inscricao_estadual=dados.get('ie_emitente') or None,
                    uf_origem=dados.get('uf_origem') or None,
                    municipio_emitente_ibge=dados.get('codigo_municipio_origem') or None,
                    cep_emitente=dados.get('cep_emitente') or None,
                    endereco_emitente=dados.get('logradouro_emitente') or None,
                    numero_nota=dados.get('numero_nf') or None,
                    chave_nfe=chave_nfe,
                    data_emissao_nota=data_emissao_nota,
                    descricao_produto=dados.get('produto_predominante') or None,
                    natureza_receita=dados.get('natureza_receita') or 'venda',
                    tipo_operacao=dados.get('tipo_operacao') or 'venda',
                    codigo_municipio_destino=dados.get('codigo_municipio_destino') or None,
                    inscricao_estadual_destinatario=dados.get('ie_destinatario') or None,
                    # Dados do destinatário
                    cnpj_destinatario=dados.get('cnpj_destinatario') or None,
                    razao_social_destinatario=dados.get('razao_destinatario') or None,
                    uf_destino=dados.get('uf_destino') or None,
                    municipio_destinatario_ibge=dados.get('municipio_destinatario') or None,
                    cep_destinatario=dados.get('cep_destinatario') or None,
                    endereco_destinatario=dados.get('logradouro_destinatario') or None,
                    # Dados do ICMS
                    icms_tipo=dados.get('icms_tipo') or None,
                    icms_base=dados.get('icms_base') or None,
                    icms_aliquota=dados.get('icms_aliquota') or None,
                    icms_valor=dados.get('icms_valor') or None,
                    # Dados do DIFAL
                    difal_valor_destino=dados.get('difal_valor_destino') or None,
                    difal_valor_remetente=dados.get('difal_valor_remetente') or None,
                    difal_base_calculo=dados.get('difal_base_calculo') or None,
                    difal_aliquota_destino=dados.get('difal_aliquota_destino') or None,
                    difal_aliquota_interestadual=dados.get('difal_aliquota_interestadual') or None,
                    difal_percentual_partilha=dados.get('difal_percentual_partilha') or None
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

        # Adicionar atividade recente
        try:
            atividade_recentes = AtividadesRecentes(
                user_id=payload['user_id'],
                type="info",
                descricao=f"Foram adicionadas {len(nfes_salvas)} NFes e {len(erros)} deram erro",
            )
            db.session.add(atividade_recentes)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Log do erro mas não interromper o fluxo
            print(f"Erro ao salvar atividade recente: {str(e)}")

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
