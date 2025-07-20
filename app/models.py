from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal
from sqlalchemy.types import Numeric

db = SQLAlchemy()

def now_sp():
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _senha = db.Column('senha', db.String(255), nullable=False)
    data_created = db.Column(db.DateTime, nullable=False, default=now_sp)

    @property
    def senha(self):
        return self._senha

    @senha.setter
    def senha(self, senha_plana):
        self._senha = generate_password_hash(senha_plana)

    def verificar_senha(self, senha_plana):
        return check_password_hash(self._senha, senha_plana)

    def __repr__(self):
        return f'<Usuario {self.username}>'
    

class UsuarioDados(db.Model):
    __tablename__ = 'usuarios_dados'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    razao_social = db.Column(db.String(255), nullable=True)
    cnpj = db.Column(db.String(14), nullable=True, unique=True)
    endereco = db.Column(db.String(255), nullable=True)
    inscricao_estadual = db.Column(db.String(30), nullable=True)
    whatsapp = db.Column(db.String(15), nullable=True)
    telefone = db.Column(db.String(15), nullable=True)

    usuario = db.relationship('Usuario', backref='dados')

class AtividadesRecentes(db.Model):
    __tablename__ = 'atividades_recentes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False) # Ex: 'success', 'danger', 'info', 'warning', 'error'
    descricao = db.Column(db.String(255), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False, default=now_sp)

    usuario = db.relationship('Usuario', backref='atividades_recentes')

class TabelaICMS(db.Model):
    __tablename__ = 'tabela_icms'
    uf = db.Column(db.String(2), primary_key=True)
    aliquota_icms = db.Column(Numeric(10, 4), nullable=False)

class CertificadoDigital(db.Model):
    __tablename__ = 'certificados_digitais'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    _senha = db.Column('senha', db.String(255), nullable=False)
    data_upload = db.Column(db.DateTime, nullable=False, default=now_sp)

    @property
    def senha(self):
        return self._senha

    @senha.setter
    def senha(self, senha_plana):
        self._senha = generate_password_hash(senha_plana)

    def verificar_senha(self, senha_plana):
        return check_password_hash(self._senha, senha_plana)

    usuario = db.relationship('Usuario', backref='certificados')
    

class NFexportdas(db.Model):
    __tablename__ = 'notas_fiscais_exportadas'

    # Identificador único da guia
    chave_nfe = db.Column(db.String(44), nullable=False, primary_key=True)

    # User ID do usuário que criou a guia
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Dados da nota fiscal
    numero_nota = db.Column(db.String(30), nullable=True)
    data_emissao_nota = db.Column(db.Date, nullable=True)

    # Dados da GNRE
    uf_favorecida = db.Column(db.String(2), nullable=True)  # Ex: 'SP'
    codigo_receita = db.Column(db.String(20), nullable=True)  # Ex: '100099'
    valor_total_nota = db.Column(db.Numeric(15, 2), nullable=True)
    mes_referencia = db.Column(db.Integer, nullable=True)
    ano_referencia = db.Column(db.Integer, nullable=True)

    # Dados do emitente (contribuinte)
    cnpj_emitente = db.Column(db.String(18), nullable=True)
    razao_social_emitente = db.Column(db.String(255), nullable=True)
    inscricao_estadual = db.Column(db.String(30), nullable=True)
    uf_origem = db.Column(db.String(2), nullable=True)
    municipio_emitente_ibge = db.Column(db.String(20), nullable=True)
    cep_emitente = db.Column(db.String(15), nullable=True)
    endereco_emitente = db.Column(db.String(500), nullable=True)

    # Dados do destinatario
    cnpj_destinatario = db.Column(db.String(18), nullable=True)  # Pode ser CPF ou CNPJ
    razao_social_destinatario = db.Column(db.String(255), nullable=True)
    uf_destino = db.Column(db.String(2), nullable=True)
    municipio_destinatario_ibge = db.Column(db.String(50), nullable=True)
    cep_destinatario = db.Column(db.String(15), nullable=True)
    endereco_destinatario = db.Column(db.String(500), nullable=True)

    # Impostos
    icms_tipo = db.Column(db.String(30), nullable=True)  # Ex: 'ICMS'
    icms_base = db.Column(db.Numeric(15, 2), nullable=True)  # Base de cálculo do ICMS
    icms_aliquota = db.Column(db.Numeric(5, 2), nullable=True)  # Ex: 18.00
    icms_valor = db.Column(db.Numeric(15, 2), nullable=True)  # Valor do ICMS destacado
    
    # Dados do DIFAL
    difal_valor_destino = db.Column(db.Numeric(15, 2), nullable=True)  # Valor do ICMS devido à UF de destino
    difal_valor_remetente = db.Column(db.Numeric(15, 2), nullable=True)  # Valor do ICMS devido à UF do remetente
    difal_base_calculo = db.Column(db.Numeric(15, 2), nullable=True)  # Base de cálculo do DIFAL
    difal_aliquota_destino = db.Column(db.Numeric(5, 2), nullable=True)  # Alíquota do ICMS da UF de destino
    difal_aliquota_interestadual = db.Column(db.Numeric(5, 2), nullable=True)  # Alíquota interestadual
    difal_percentual_partilha = db.Column(db.Numeric(5, 2), nullable=True)  # Percentual de partilha

    # Campos complementares
    descricao_produto = db.Column(db.String(500), nullable=True)
    natureza_receita = db.Column(db.String(150), nullable=True)
    tipo_operacao = db.Column(db.String(30), nullable=True)  # Ex: 'venda', 'remessa'
    codigo_municipio_destino = db.Column(db.String(20), nullable=True)  # código IBGE
    inscricao_estadual_destinatario = db.Column(db.String(30), nullable=True)

    # Controle
    data_created = db.Column(db.DateTime, nullable=False, default=now_sp)
    data_updated = db.Column(db.DateTime, nullable=False, default=now_sp, onupdate=now_sp)
    status = db.Column(db.String(30), nullable=False, default='pendente')  # Ex: 'pendente', 'gerado', 'pago', 'cancelado'


class GnreGuia(db.Model):
    __tablename__ = 'gnre_guias'

    id = db.Column(db.Integer, primary_key=True)
    chave_nfe = db.Column(db.String(44), db.ForeignKey('notas_fiscais_exportadas.chave_nfe'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_emissao = db.Column(db.DateTime, nullable=False, default=now_sp)
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)

    numero_guia = db.Column(db.String(100))
    uf_favorecida = db.Column(db.String(2))
    codigo_receita = db.Column(db.String(20))
    situacao = db.Column(db.String(30))
    linha_digitavel = db.Column(db.String(200))
    url_pdf = db.Column(db.String(1000))
    data_pagamento = db.Column(db.DateTime, nullable=True)
    valor_pago = db.Column(db.Numeric(15, 2), nullable=True)

    nf = db.relationship('NFexportdas', backref='gnre_guias')
    usuario = db.relationship('Usuario', backref='gnre_guias')
