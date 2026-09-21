import random
from datetime import timedelta, datetime

import data
from flask import Flask, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models import Funcionario, db_session, Fornecedor, Movimento, Pastilha
import os
from dotenv import load_dotenv
# Gerar Token
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from functools import wraps

# 3jUU

# carregar variaveis de ambiente
load_dotenv()
app = Flask(__name__)
# definir a senha, em produção colocar em local seguro
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
jwt = JWTManager(app)

# previne gargalo "too many connections"
"""
    ### @app.teardown_appcontext (O Zelador)
    ### Para que serve: 
    Fechar conexões de banco de dados, limpar memória temporária, fechar arquivos abertos. 
    Ele evita o temido Memory Leak (Vazamento de Memória).
    ### Curiosidade: 
    Como estamos usando o Flask-SQLAlchemy, você nunca precisará escrever esse comando na mão para o banco de dados. 
    A biblioteca já injeta um teardown_appcontext invisível no seu app que faz db.session.remove() automaticamente.
    """


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


""" Não mexer - PADRÃO, segue o login """


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        print(f"current_user:{current_user}")

        try:
            sql = select(Funcionario).where(Funcionario.id == current_user)
            funcionario_existente = db_session.execute(sql).scalar()
            print(f'Funcionario existente: {funcionario_existente}')
            # print(f'teste: {funcionario_existente.papel == "admin"}')
            if funcionario_existente and funcionario_existente.papel == "admin":
                return fn(*args, **kwargs)
            dado = {
                "msg": "Acesso negado: Requer privilégio de administrador"
            }
            return jsonify(dado), 403
        except Exception as e:
            print("Erro admin_required:", e)
            dado = {
                "msg": "Erro ao verificar privilégio"
            }
            return jsonify(dado), 404

    return wrapper


@app.route('/', methods=['GET'])
def principal():
    print(f"def_identificacaoxx {str(datetime.now())}")
    dados = {
        "msg": "COD: 3jUU",
        "atualizado_em": str(datetime.now())
    }
    return jsonify(dados), 200


@app.route('/login', methods=['POST'])
def login():
    try:
        dados_entrada = request.get_json()
        if not dados_entrada:
            return jsonify({"msg": "JSON inválido"}), 400

        email = dados_entrada.get("email")
        if not email:
            return jsonify({"msg": "Email é obrigatório"}), 400

        senha = dados_entrada.get("senha")
        if not senha:
            return jsonify({"msg": "Senha é obrigatório"})

        sql = select(Funcionario).where(Funcionario.email == email)
        funcionario_existente = db_session.execute(sql).scalar()
        if not funcionario_existente:
            return jsonify({"msg": "Email não cadastrado"}), 401

        if funcionario_existente and funcionario_existente.check_password_hash(senha):
            # criação e configurar Token
            access_token = create_access_token(
                identity=str(funcionario_existente.id),
                additional_claims={
                    "id": str(funcionario_existente.id),
                    "papel": funcionario_existente.papel,
                    "nome": funcionario_existente.nome,
                    "token_criado_em": str(datetime.now())
                },
                expires_delta=timedelta(minutes=30)
            )
            dados = {
                "access_token": access_token,
            }
            return jsonify(dados), 200
        dados = {
            "msg": "Credenciais invalidas"
        }
        return jsonify(dados), 401

    except Exception as e:
        print("Erro login:", e)
        dados = {
            "msg": "Erro ao logar"
        }
        return jsonify(dados), 400


@app.route('/usuarios', methods=['POST'])
def cadastro():
    print("def_user_post")
    dados = request.get_json()
    print("dados_recebido: ", dados)
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')
    papel = dados.get('papel', 'usuario')

    if not nome or not email or not senha:
        dados = {
            "msg": "Email, usuário e senha são obrigatórios"
        }
        return jsonify(dados), 400

    try:
        # Verificar se o usuário já existe
        user_check = select(Funcionario).where(Funcionario.email == email)
        usuario_existente = db_session.execute(user_check).scalar()

        if usuario_existente:
            dados = {
                "msg": "Usuário já existe"
            }
            return jsonify(dados), 409

        novo_usuario = Funcionario(nome=nome, email=email, papel=papel)
        novo_usuario.set_senha_hash(senha)
        db_session.add(novo_usuario)
        db_session.commit()

        dados = {
            "msg": "Usuário criado com sucesso",
            "user_id": novo_usuario.id
        }
        return jsonify(dados), 201
    except Exception as e:
        db_session.rollback()
        print("erro500: ", e)
        dados = {
            "msg": f"Erro ao registrar usuário: {str(e)}"
        }
        return jsonify(dados), 500


@app.route('/cadastro_funcionario', methods=['POST'])
def cadastro_funcionario():
    dados = request.get_json()
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')

    if not nome or not email or not senha:
        return jsonify({"msg": "Todos os dados são obrigatórios"}), 400

    db_session()
    try:
        user_check = select(Funcionario).where(Funcionario.email == email)
        funcionario_existente = db_session.execute(user_check).scalars().one_or_none()

        if funcionario_existente:
            return jsonify({"msg": "Funcionario já existe"}), 409

        novo_funcionario = Funcionario(
            nome=nome,
            email=email,
            senha=senha
        )
        novo_funcionario.set_password(senha)
        db_session.add(novo_funcionario)
        db_session.commit()

        user_id = novo_funcionario.id
        return jsonify({"msg": "Funcionario cadastrado com sucesso", "user_id": user_id}), 201

    except Exception as e:
        db_session.rollback()
        return jsonify({"msg": f"Erro ao registrar funcionario: {str(e)}"}), 500

@app.route('/cadastro_fornecedor', methods=['POST'])
def cadastro_fornecedor():
    dados = request.get_json()
    nome = dados.get('nome')
    cnpj = dados.get('cnpj')
    email = dados.get('email')

    if not nome or not cnpj or not email:
        return jsonify({"msg": "Todos os dados são obrigatórios"}), 400

    db_session()
    try:
        user_check = select(Fornecedor).where(Fornecedor.cnpj == cnpj)
        fornecedor_existente = db_session.execute(user_check).scalars().one_or_none()

        if fornecedor_existente:
            return jsonify({"msg": "Fornecedor já existe"}), 409

        novo_fornecedor = Fornecedor(
            nome=nome,
            cnpj=cnpj,
            email=email
        )
        db_session.add(novo_fornecedor)
        db_session.commit()

        user_id = novo_fornecedor.id
        return jsonify({"msg": "Fornecedor cadastrado com sucesso", "user_id": user_id}), 201

    except Exception as e:
        db_session.rollback()
        return jsonify({"msg": f"Erro ao registrar fornecedor: {str(e)}"}), 500

@app.route('/cadastro_pastilha', methods=['POST'])
def cadastro_pastilha():
    dados = request.get_json()
    tipo_aplicacao = dados.get('tipo_aplicacao')
    cor = dados.get('cor')
    material = dados.get('material')
    fornecedor_id = dados.get('fornecedor_id')
    data = datetime.datetime.now()

    lista = [
        "a", "b", "c", "d",
        "e", "f", "g", "h", "i",
        "j", "k", "l", "m", "n",
        "o", "p", "q", "r", "s", "u",
        "v", "w", "x", "y", "z"
    ]
    codigo1 = random.choice(lista).upper()
    codigo2 = random.choice(lista).upper()
    codigo3 = random.choice(lista).upper()
    codigo_data = str(data.timestamp()).replace('.', '')
    codigo_rastreio = codigo1 + codigo_data + codigo2 + codigo3
    print(codigo_rastreio)

    if not tipo_aplicacao or not cor or not material or not fornecedor_id or not codigo_data:
        return jsonify({"msg": "Todos os dados são obrigatórios"}), 400

    db_session()
    try:
        pastilha_check = select(Pastilha).where(Pastilha.codigo_rastreio == codigo_rastreio)
        pastilha_existente = db_session.execute(pastilha_check).scalars().one_or_none()

        if pastilha_existente:
            return jsonify({"msg": "Essa pastilha já existe"}), 409

        nova_pastilha = Pastilha(
            tipo_aplicacao=tipo_aplicacao,
            cor=cor,
            material=material,
            fornecedor_id=fornecedor_id,
        )
        db_session.add(nova_pastilha)
        db_session.commit()

        user_id = nova_pastilha.id
        return jsonify({"msg": "Pastilha cadastrada com sucesso", "user_id": user_id}), 201

    except Exception as e:
        db_session.rollback()
        return jsonify({"msg": f"Erro ao registrar pastilha: {str(e)}"}), 500

@app.route('/listar_pastilha', methods=['POST'])
def listar_pastilha():
    db_session()
    pastilha_sql = select(Pastilha)
    pastilha_resultado = db_session.execute(pastilha_sql).scalars()
    dados_pastilha = []
    for func in pastilha_resultado:
        dados_pastilha.append(func.serialize())
    return jsonify({"pastilha": dados_pastilha}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001, host="0.0.0.0")  # Rodar em uma porta diferente da API principal
