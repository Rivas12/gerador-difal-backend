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