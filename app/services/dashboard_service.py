from flask import jsonify
from app.models import db, NFexportdas, AtividadesRecentes
from datetime import datetime, timedelta

def obter_dashboard_usuario(payload):
    """Obtém os dados do dashboard do usuário"""
    try:
        user_id = payload['user_id']
        
        # NFes Exportadas (total de NFes do usuário)
        nfes_exportadas = db.session.query(NFexportdas).filter_by(user_id=user_id).count()
        
        # Valor Total (soma de todas as notas)
        valor_total_result = db.session.query(db.func.sum(NFexportdas.valor_total_nota)).filter_by(user_id=user_id).scalar()
        valor_total = float(valor_total_result) if valor_total_result else 0.0
        
        # Pendentes (notas com status pendente)
        pendentes = db.session.query(NFexportdas).filter_by(user_id=user_id, status='pendente').count()
        
        # Valor Médio (valor total dividido pelo número de NFes)
        valor_medio = valor_total / nfes_exportadas if nfes_exportadas > 0 else 0.0
        
        # Atividades Recentes (últimas 10 atividades ordenadas por data de criação)
        atividades_recentes = []
        atividades_recentes_query = db.session.query(AtividadesRecentes).filter_by(user_id=user_id).order_by(AtividadesRecentes.data_hora.desc()).limit(10).all()

        for atividade in atividades_recentes_query:
            # Calcular tempo decorrido de forma mais precisa
            if atividade.data_hora:
                agora = datetime.now()
                diferenca = agora - atividade.data_hora
                
                # Verificar se é o mesmo dia (comparando apenas a data)
                if atividade.data_hora.date() == agora.date():
                    tempo_texto = "Hoje"
                # Verificar se foi ontem
                elif atividade.data_hora.date() == (agora - timedelta(days=1)).date():
                    tempo_texto = "Ontem"
                # Se foi há mais de um dia
                else:
                    tempo_texto = atividade.data_hora.strftime("%d/%m/%Y")

            else:
                tempo_texto = "Data não disponível"
            
            # Determinar status da atividade baseado no type
            status_icon = atividade.type  # 'success', 'danger', 'info', 'warning', 'error'
            
            atividades_recentes.append({
                'titulo': atividade.descricao,
                'tempo': tempo_texto,
                'status': status_icon,
                'type': atividade.type
            })
        
        return jsonify({
            'nf_exportadas': nfes_exportadas,
            'valor_total': valor_total,
            'pendentes': pendentes,
            'valor_medio': valor_medio,
            'atividades_recentes': atividades_recentes
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao buscar dados do dashboard: {str(e)}'}), 500

def verificar_status_api():
    """Verifica o status da API e do banco de dados"""
    from sqlalchemy import text
    
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
