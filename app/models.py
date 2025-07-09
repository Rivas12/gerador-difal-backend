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

class TabelaICMS(db.Model):
    __tablename__ = 'tabela_icms'
    uf = db.Column(db.String(2), primary_key=True)
    aliquota_icms = db.Column(Numeric(10, 4), nullable=False)
    

class NFexportdas(db.Model):
    __tablename__ = 'notas_fiscais_exportadas'

    # Identificador único da guia
    chave_nfe = db.Column(db.String(44), nullable=False, primary_key=True)

    # User ID do usuário que criou a guia
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Dados da nota fiscal
    numero_nota = db.Column(db.String(20), nullable=True)
    data_emissao_nota = db.Column(db.Date, nullable=True)

    # Dados da GNRE
    uf_favorecida = db.Column(db.String(2), nullable=False)  # Ex: 'SP'
    codigo_receita = db.Column(db.String(10), nullable=False)  # Ex: '100099'
    valor_total_nota = db.Column(db.Numeric(10, 2), nullable=True)
    mes_referencia = db.Column(db.Integer, nullable=False)
    ano_referencia = db.Column(db.Integer, nullable=False)

    # Dados do emitente (contribuinte)
    cnpj_emitente = db.Column(db.String(14), nullable=False)
    razao_social_emitente = db.Column(db.String(255), nullable=False)
    inscricao_estadual = db.Column(db.String(20), nullable=True)
    uf_origem = db.Column(db.String(2), nullable=True)
    municipio_emitente_ibge = db.Column(db.String(7), nullable=True)
    cep_emitente = db.Column(db.String(10), nullable=True)
    endereco_emitente = db.Column(db.String(255), nullable=True)

    # Impostos
    icms_tipo = db.Column(db.String(20), nullable=True)  # Ex: 'ICMS'
    icms_base = db.Column(db.Numeric(10, 2), nullable=True)  # Base de cálculo do ICMS
    icms_aliquota = db.Column(db.Numeric(5, 2), nullable=True)  # Ex: 18.00
    icms_valor = db.Column(db.Numeric(10, 2), nullable=True)  # Valor do ICMS destacado

    # Campos complementares
    descricao_produto = db.Column(db.String(255), nullable=True)
    natureza_receita = db.Column(db.String(80), nullable=True)
    tipo_operacao = db.Column(db.String(20), nullable=True)  # Ex: 'venda', 'remessa'
    codigo_municipio_destino = db.Column(db.String(7), nullable=True)  # código IBGE
    inscricao_estadual_destinatario = db.Column(db.String(20), nullable=True)

    # Controle
    data_created = db.Column(db.DateTime, nullable=False, default=now_sp)
    data_updated = db.Column(db.DateTime, nullable=False, default=now_sp, onupdate=now_sp)
    status = db.Column(db.String(20), nullable=False, default='pendente')  # Ex: 'pendente', 'gerado', 'pago', 'cancelado'


class GnreGuia(db.Model):
    __tablename__ = 'gnre_guias'

    id = db.Column(db.Integer, primary_key=True)
    chave_nfe = db.Column(db.String(44), db.ForeignKey('notas_fiscais_exportadas.chave_nfe'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_emissao = db.Column(db.DateTime, nullable=False, default=now_sp)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)

    numero_guia = db.Column(db.String(50))
    uf_favorecida = db.Column(db.String(2))
    codigo_receita = db.Column(db.String(10))
    situacao = db.Column(db.String(20))
    linha_digitavel = db.Column(db.String(100))
    url_pdf = db.Column(db.String(500))
    data_pagamento = db.Column(db.DateTime, nullable=True)
    valor_pago = db.Column(db.Numeric(10, 2), nullable=True)

    nf = db.relationship('NFexportdas', backref='gnre_guias')
    usuario = db.relationship('Usuario', backref='gnre_guias')
