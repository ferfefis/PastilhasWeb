from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session, relationship
from werkzeug.security import generate_password_hash, check_password_hash

"""
##Base de dados link local(model) SQLITE
"""
engine = create_engine('mysql+pymysql://root:senaisp@localhost:3306/dda', pool_size=10, max_overflow=20)

# Banco MySQL
Base = declarative_base()

db_session = scoped_session(sessionmaker(bind=engine))

class Pastilha(Base):
    __tablename__ = 'pastilha'
    id = Column(Integer, primary_key=True)
    tipo_aplicacao = Column(String(100), nullable=False)
    cor = Column(String(100), nullable=False)
    material = Column(String(100), nullable=False)
    fornecedor_id = Column(Integer, ForeignKey('fornecedor.id'))
    criado_em = Column(DateTime, nullable=False, server_default=func.now())

    def serialize(self):
        dados = {
            "id": self.id,
            "tipo_aplicacao": self.tipo_aplicacao,
            "cor": self.cor,
            "material": self.material,
            "fornecedor_id": self.fornecedor_id,
            "criado_em": self.criado_em,
        }
        return dados

class Funcionario(Base):
    __tablename__ = 'funcionario'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    senha = Column(String(255), nullable=False)
    criado_em = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return f'<Funcionario {self.nome}>'

    def set_password(self, password):
        self.senha = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha, password)

    def serialize(self):
        dados = {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "senha": self.senha,
            "criado_em": self.criado_em,
        }
        return dados

class Fornecedor(Base):
    __tablename__ = 'fornecedor'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    cnpj = Column(String(100), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    criado_em = Column(DateTime, nullable=False, server_default=func.now())

    def serialize(self):
        dados = {
            "id": self.id,
            "nome": self.nome,
            "cnpj": self.cnpj,
            "email": self.email,
            "criado_em": self.criado_em,
        }
        return dados


class Movimento(Base):
    __tablename__ = 'movimentacao'
    id = Column(Integer, primary_key=True)
    data_movimentacao = Column(DateTime, nullable=False, server_default=func.now())
    tipo = Column(String(7), nullable=False)
    quantidade = Column(Integer, nullable=False)
    pastilha_id = Column(Integer, ForeignKey('pastilha.id'))
    criado_em = Column(DateTime, nullable=False, server_default=func.now())

    def serialize(self):
        dados = {
            "id": self.id,
            "data_movimentacao": self.data_movimentacao,
            "tipo": self.tipo,
            "quantidade": self.quantidade,
            "pastilha_id": self.pastilha_id,
            "criado_em": self.criado_em,
        }
        return dados

if __name__ == "__main__":
    # create_tables()
    print("Tabelas criadas no banco portal.sqlite3!")
