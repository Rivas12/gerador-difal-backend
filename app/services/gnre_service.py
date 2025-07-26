from flask import jsonify
from app.models import db, GnreGuia, NFexportdas
from sqlalchemy.orm import joinedload
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def listar_guias_usuario(payload):
    """
    Lista todas as guias GNRE do usuário com dados relacionados da NFe
    """
    try:
        user_id = payload.get('user_id')
        
        if not user_id:
            return jsonify({'erro': 'ID do usuário não encontrado no token'}), 400

        # Busca as guias com os dados da NFe relacionada usando joinedload para otimizar
        guias = GnreGuia.query.options(joinedload(GnreGuia.nf))\
            .filter_by(user_id=user_id)\
            .order_by(GnreGuia.data_emissao.desc())\
            .all()

        # Monta a lista de guias com os dados da NFe
        lista_guias = []
        for guia in guias:
            guia_data = {
                'id': guia.id,
                'chave_nfe': guia.chave_nfe,
                'numero_guia': guia.numero_guia,
                'data_emissao': guia.data_emissao.isoformat() if guia.data_emissao else None,
                'valor_total': float(guia.valor_total) if guia.valor_total else 0,
                'uf_favorecida': guia.uf_favorecida,
                'codigo_receita': guia.codigo_receita,
                'situacao': guia.situacao,
                'linha_digitavel': guia.linha_digitavel,
                'url_pdf': guia.url_pdf,
                'data_pagamento': guia.data_pagamento.isoformat() if guia.data_pagamento else None,
                'valor_pago': float(guia.valor_pago) if guia.valor_pago else None,
                
                # Dados da NFe relacionada
                'nfe': {
                    'numero_nota': guia.nf.numero_nota if guia.nf else None,
                    'data_emissao_nota': guia.nf.data_emissao_nota.isoformat() if guia.nf and guia.nf.data_emissao_nota else None,
                    'razao_social_emitente': guia.nf.razao_social_emitente if guia.nf else None,
                    'cnpj_emitente': guia.nf.cnpj_emitente if guia.nf else None,
                    'razao_social_destinatario': guia.nf.razao_social_destinatario if guia.nf else None,
                    'cnpj_destinatario': guia.nf.cnpj_destinatario if guia.nf else None,
                    'uf_origem': guia.nf.uf_origem if guia.nf else None,
                    'uf_destino': guia.nf.uf_destino if guia.nf else None,
                    'valor_total_nota': float(guia.nf.valor_total_nota) if guia.nf and guia.nf.valor_total_nota else 0,
                    'status': guia.nf.status if guia.nf else None
                } if guia.nf else None
            }
            lista_guias.append(guia_data)

        return jsonify({
            'sucesso': True,
            'guias': lista_guias,
            'total': len(lista_guias)
        }), 200

    except Exception as e:
        logger.error(f"Erro ao listar guias do usuário {payload.get('user_id', 'N/A')}: {str(e)}")
        return jsonify({
            'erro': 'Erro interno do servidor ao listar guias',
            'detalhes': str(e)
        }), 500


def obter_guia_por_id(payload, guia_id):
    """
    Obtém uma guia específica com todos os dados da NFe relacionada
    """
    try:
        user_id = payload.get('user_id')
        
        if not user_id:
            return jsonify({'erro': 'ID do usuário não encontrado no token'}), 400

        # Busca a guia específica do usuário
        guia = GnreGuia.query.options(joinedload(GnreGuia.nf))\
            .filter_by(id=guia_id, user_id=user_id)\
            .first()

        if not guia:
            return jsonify({'erro': 'Guia não encontrada'}), 404

        guia_data = {
            'id': guia.id,
            'chave_nfe': guia.chave_nfe,
            'numero_guia': guia.numero_guia,
            'data_emissao': guia.data_emissao.isoformat() if guia.data_emissao else None,
            'valor_total': float(guia.valor_total) if guia.valor_total else 0,
            'uf_favorecida': guia.uf_favorecida,
            'codigo_receita': guia.codigo_receita,
            'situacao': guia.situacao,
            'linha_digitavel': guia.linha_digitavel,
            'url_pdf': guia.url_pdf,
            'data_pagamento': guia.data_pagamento.isoformat() if guia.data_pagamento else None,
            'valor_pago': float(guia.valor_pago) if guia.valor_pago else None,
            
            # Dados completos da NFe relacionada
            'nfe': {
                'chave_nfe': guia.nf.chave_nfe,
                'numero_nota': guia.nf.numero_nota,
                'data_emissao_nota': guia.nf.data_emissao_nota.isoformat() if guia.nf.data_emissao_nota else None,
                'razao_social_emitente': guia.nf.razao_social_emitente,
                'cnpj_emitente': guia.nf.cnpj_emitente,
                'inscricao_estadual': guia.nf.inscricao_estadual,
                'uf_origem': guia.nf.uf_origem,
                'endereco_emitente': guia.nf.endereco_emitente,
                'razao_social_destinatario': guia.nf.razao_social_destinatario,
                'cnpj_destinatario': guia.nf.cnpj_destinatario,
                'uf_destino': guia.nf.uf_destino,
                'endereco_destinatario': guia.nf.endereco_destinatario,
                'valor_total_nota': float(guia.nf.valor_total_nota) if guia.nf.valor_total_nota else 0,
                'icms_valor': float(guia.nf.icms_valor) if guia.nf.icms_valor else 0,
                'difal_valor_destino': float(guia.nf.difal_valor_destino) if guia.nf.difal_valor_destino else 0,
                'difal_valor_remetente': float(guia.nf.difal_valor_remetente) if guia.nf.difal_valor_remetente else 0,
                'status': guia.nf.status
            } if guia.nf else None
        }

        return jsonify({
            'sucesso': True,
            'guia': guia_data
        }), 200

    except Exception as e:
        logger.error(f"Erro ao obter guia {guia_id} do usuário {payload.get('user_id', 'N/A')}: {str(e)}")
        return jsonify({
            'erro': 'Erro interno do servidor ao obter guia',
            'detalhes': str(e)
        }), 500
