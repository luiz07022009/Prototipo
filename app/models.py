from app import db
from datetime import datetime, timedelta, time
import uuid

# --- Tabelas de Associação ---
user_instituicoes = db.Table(
    'user_instituicoes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('instituicao_id', db.Integer, db.ForeignKey('instituicoes.id'), primary_key=True)
)

admin_instituicoes = db.Table(
    'admin_instituicoes',
    db.Column('admin_id', db.Integer, db.ForeignKey('admins.id'), primary_key=True),
    db.Column('instituicao_id', db.Integer, db.ForeignKey('instituicoes.id'), primary_key=True)
)

# --- Mixin para Modelos com Campos em Comum ---
class AccountMixin:
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    active_inst_id = db.Column(db.Integer, db.ForeignKey('instituicoes.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'cpf': self.cpf,
            'active_inst_id': self.active_inst_id
        }

# --- Modelos Principais ---
class User(db.Model, AccountMixin):
    __tablename__ = 'users'
    reservas = db.relationship('Reserva', backref='user', lazy=True, cascade="all, delete-orphan")
    instituicoes = db.relationship('Instituicao', secondary=user_instituicoes, back_populates='membros')

class Admin(db.Model, AccountMixin):
    __tablename__ = 'admins'
    instituicoes = db.relationship('Instituicao', secondary=admin_instituicoes, back_populates='admins')

class Instituicao(db.Model):
    __tablename__ = 'instituicoes'
    id = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    token = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    espacos = db.relationship('Espaco', backref='instituicao', lazy=True, cascade="all, delete-orphan")
    membros = db.relationship('User', secondary=user_instituicoes, back_populates='instituicoes')
    admins = db.relationship('Admin', secondary=admin_instituicoes, back_populates='instituicoes')

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cnpj': self.cnpj,
            'email': self.email,
            'token': self.token
        }

class Espaco(db.Model):
    __tablename__ = 'espacos'
    id = db.Column(db.Integer, primary_key=True)
    id_inst = db.Column(db.Integer, db.ForeignKey('instituicoes.id'), nullable=False)
    nome = db.Column(db.String(80), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200), nullable=True)
    multi_reservas = db.Column(db.Boolean, default=False, nullable=False)
    disponibilidade = db.Column(db.Boolean, default=True, nullable=False)
    duracao_padrao = db.Column(db.Integer, default=30)  # minutos
    antecedencia_maxima_dias = db.Column(db.Integer, default=7)
    reservas = db.relationship('Reserva', backref='espaco', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'id_inst': self.id_inst,
            'nome': self.nome,
            'tipo': self.tipo,
            'descricao': self.descricao,
            'multi_reservas': self.multi_reservas,
            'disponibilidade': self.disponibilidade,
            'duracao_padrao': self.duracao_padrao,
            'antecedencia_maxima_dias': self.antecedencia_maxima_dias
        }

class Reserva(db.Model):
    __tablename__ = 'reservas'
    id = db.Column(db.Integer, primary_key=True)
    id_espaco = db.Column(db.Integer, db.ForeignKey('espacos.id'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_reserva = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    observacoes = db.Column(db.String(300), nullable=True)

    def to_dict_history(self):
        return {
            'id': self.id,
            'data_reserva': self.data_reserva.strftime('%d/%m/%Y'),
            'hora_inicio': self.hora_inicio.strftime('%H:%M'),
            'hora_fim': self.hora_fim.strftime('%H:%M'),
            'observacoes': self.observacoes,
            'espaco_nome': self.espaco.nome,
            'user_nome': self.user.nome,
            'user_email': self.user.email,
            'user_cpf': self.user.cpf
        }

# --- Função Auxiliar ---
def gerar_slots(duracao=30):
    """Gera uma lista de tuplas (hora_inicio, hora_fim) para um dia padrão."""
    inicio = time(8, 0)
    fim = time(22, 0)
    atual = datetime.combine(datetime.today(), inicio)
    horarios = []
    while atual.time() < fim:
        proximo = (atual + timedelta(minutes=duracao)).time()
        horarios.append((atual.time(), proximo))
        atual += timedelta(minutes=duracao)
    return horarios
