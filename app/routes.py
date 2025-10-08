from flask import Flask, render_template, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
from app.models import User, Admin, Instituicao, Espaco, Reserva

# app = Flask(__name__)

def init_routes(app):

    # --- ROTAS HTML ---
    @app.route('/')
    def home():
        return render_template('pag_user.html')

    @app.route('/admin')
    def admin_panel():
        return render_template('pag_adm.html')

    @app.route('/planos')
    def planos():
        return render_template('pag_planos.html')


# ----------------- CRIAR INSTITUIÇÃO -----------------
    @app.route('/api/instituicoes', methods=['POST'])
    def criar_instituicao():
        data = request.get_json()
        print("📦 Dados recebidos:", data)  # <--- DEBUG

        nome = data.get('nome')
        cnpj = data.get('cnpj')
        email = data.get('email')
        admin_id = data.get('admin_id')

        if not all([nome, cnpj, email, admin_id]):
            return jsonify({'erro': 'Campos obrigatórios faltando.'}), 400

        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({'erro': 'Admin não encontrado.'}), 404

        inst_existente = Instituicao.query.filter_by(cnpj=cnpj).first()
        if inst_existente:
            return jsonify({'erro': 'Instituição com este CNPJ já existe.'}), 409

        nova_inst = Instituicao(nome=nome, cnpj=cnpj, email=email)
        db.session.add(nova_inst)
        db.session.commit()

        admin.id_inst = nova_inst.id
        db.session.commit()

        return jsonify({
            'mensagem': 'Instituição criada e vinculada ao admin com sucesso.',
            'instituicao': {
                'id': nova_inst.id,
                'nome': nova_inst.nome,
                'cnpj': nova_inst.cnpj,
                'email': nova_inst.email
            }
        }), 201


# ----------------- LISTAR INSTITUIÇÕES -----------------
    @app.route('/api/instituicoes', methods=['GET'])
    def listar_instituicoes():
        cnpj = request.args.get('cnpj')
        if cnpj:
            insts = Instituicao.query.filter_by(cnpj=cnpj).all()
        else:
            insts = Instituicao.query.all()

        return jsonify([
            {'id': i.id, 'nome': i.nome, 'cnpj': i.cnpj, 'email': i.email}
            for i in insts
        ])


# ----------------- VINCULAR ADMIN MANUALMENTE -----------------
    @app.route('/api/instituicoes/vincular', methods=['POST'])
    def vincular_instituicao():
        data = request.get_json()
        print("📦 Dados de vinculação:", data)  # <--- DEBUG

        admin_id = data.get('admin_id')
        inst_id = data.get('inst_id')

        admin = Admin.query.get(admin_id)
        inst = Instituicao.query.get(inst_id)
        if not admin or not inst:
            return jsonify({'erro': 'Admin ou instituição não encontrados.'}), 404

        admin.id_inst = inst.id
        db.session.commit()

        return jsonify({'mensagem': f'{admin.nome} vinculado à instituição {inst.nome}.'}), 200


    # --- API: ESPAÇOS ---
    @app.route('/api/espacos', methods=['GET'])
    def get_espacos():
        espacos = Espaco.query.all()
        return jsonify([e.to_dict() for e in espacos]), 200


    @app.route('/api/espacos', methods=['POST'])
    def create_espaco():
        data = request.get_json()
        if not data or not all(k in data for k in ['id_inst', 'nome', 'tipo']):
            abort(400, description="Faltando 'id_inst', 'nome' ou 'tipo'.")

        novo_espaco = Espaco(
            id_inst=data['id_inst'],
            nome=data['nome'],
            tipo=data['tipo'],
            descricao=data.get('descricao', ''),
            multi_reservas=data.get('multi_reservas', False),
            disponibilidade=data.get('disponibilidade', True),
            duracao_padrao=data.get('duracao_padrao', 30),
            antecedencia_maxima_dias=data.get('antecedencia_maxima_dias', 7)
        )

        db.session.add(novo_espaco)
        db.session.commit()

        return jsonify(novo_espaco.to_dict()), 201


    @app.route('/api/espacos/<int:id>', methods=['PUT'])
    def update_espaco(id):
        espaco = Espaco.query.get_or_404(id)
        data = request.get_json()

        espaco.nome = data.get('nome', espaco.nome)
        espaco.descricao = data.get('descricao', espaco.descricao)
        espaco.tipo = data.get('tipo', espaco.tipo)
        espaco.disponibilidade = data.get('disponibilidade', espaco.disponibilidade)
        espaco.duracao_padrao = data.get('duracao_padrao', espaco.duracao_padrao)
        espaco.antecedencia_maxima_dias = data.get('antecedencia_maxima_dias', espaco.antecedencia_maxima_dias)

        db.session.commit()
        return jsonify(espaco.to_dict()), 200


    @app.route('/api/espacos/<int:id>', methods=['DELETE'])
    def delete_espaco(id):
        espaco = Espaco.query.get_or_404(id)
        db.session.delete(espaco)
        db.session.commit()
        return jsonify({'message': 'Espaço deletado com sucesso.'}), 200


    # --- API: AUTENTICAÇÃO ---
    @app.route('/api/register/user', methods=['POST'])
    def register_user():
        data = request.get_json()
        if not data or not all(k in data for k in ['cpf', 'nome', 'email', 'senha']):
            abort(400, description="Faltando dados para cadastro de usuário.")

        if User.query.filter_by(email=data['email']).first() or Admin.query.filter_by(email=data['email']).first():
            abort(409, description="E-mail já cadastrado.")
        if User.query.filter_by(cpf=data['cpf']).first() or Admin.query.filter_by(cpf=data['cpf']).first():
            abort(409, description="CPF já cadastrado.")

        hashed_password = generate_password_hash(data['senha'], method='pbkdf2:sha256')
        new_user = User(cpf=data['cpf'], nome=data['nome'], email=data['email'], senha=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Usuário criado com sucesso!'}), 201


    @app.route('/api/register/admin', methods=['POST'])
    def register_admin():
        data = request.get_json()
        if not data or not all(k in data for k in ['cpf', 'nome', 'email', 'senha']):
            abort(400, description="Faltando dados para cadastro de administrador.")

        if User.query.filter_by(email=data['email']).first() or Admin.query.filter_by(email=data['email']).first():
            abort(409, description="E-mail já cadastrado.")
        if User.query.filter_by(cpf=data['cpf']).first() or Admin.query.filter_by(cpf=data['cpf']).first():
            abort(409, description="CPF já cadastrado.")

        hashed_password = generate_password_hash(data['senha'], method='pbkdf2:sha256')
        new_admin = Admin(cpf=data['cpf'], nome=data['nome'], email=data['email'], senha=hashed_password)
        db.session.add(new_admin)
        db.session.commit()
        return jsonify({'message': 'Administrador criado com sucesso!'}), 201


    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        if not data or not data.get('email') or not data.get('senha'):
            abort(400, description="E-mail ou senha não fornecidos.")

        user = User.query.filter_by(email=data['email']).first()
        if user and check_password_hash(user.senha, data['senha']):
            return jsonify({
                "status": "success",
                "user_type": "user",
                "user_data": user.nome
            }), 200

        admin = Admin.query.filter_by(email=data['email']).first()
        if admin and check_password_hash(admin.senha, data['senha']):
            return jsonify({
                "status": "success",
                "user_type": "admin",
                "user_data": admin.nome
            }), 200

        return jsonify({"status": "error", "message": "Credenciais inválidas."}), 401

    return app