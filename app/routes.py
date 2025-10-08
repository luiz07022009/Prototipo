from flask import render_template, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app import db
from app.models import User, Admin, Instituicao, Espaco, Reserva, gerar_slots
import uuid

def init_routes(app):

    # --- ROTAS HTML ---
    # Rotas para renderizar páginas HTML
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/home')
    def home():
        return render_template('pag_user.html')

    @app.route('/admin')
    def admin_panel():
        return render_template('pag_adm.html')

    @app.route('/planos')
    def planos():
        return render_template('pag_planos.html')


    # --- API: INSTITUIÇÕES ---
    
    @app.route('/api/instituicoes', methods=['POST'])
    def criar_instituicao():
        ''' Cria uma nova instituição e vincula ao admin '''
        data = request.get_json()
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

        token = str(uuid.uuid4())
        nova_inst = Instituicao(nome=nome, cnpj=cnpj, email=email, token=token)
        db.session.add(nova_inst)
        db.session.commit()

        admin.instituicoes.append(nova_inst)
        admin.active_inst_id = nova_inst.id
        db.session.commit()

        return jsonify({
            'mensagem': 'Instituição criada e vinculada ao admin com sucesso.',
            'instituicao': nova_inst.to_dict()
        }), 201

    @app.route('/api/instituicoes', methods=['GET'])
    def listar_instituicoes():
        ''' Lista todas as instituições ou filtra por CNPJ  '''
        cnpj = request.args.get('cnpj')
        if cnpj:
            insts = Instituicao.query.filter_by(cnpj=cnpj).all()
        else:
            insts = Instituicao.query.all()
        return jsonify([i.to_dict() for i in insts])

    @app.route('/api/instituicoes/<int:inst_id>/token', methods=['GET'])
    def get_instituicao_token(inst_id):
        ''' Retorna o token de uma instituição se o admin estiver vinculado a ela '''
        admin_id = request.args.get('admin_id', type=int)
        inst = Instituicao.query.get_or_404(inst_id)
        if admin_id:
            admin = Admin.query.get(admin_id)
            if not admin:
                return jsonify({'erro': 'Admin não encontrado.'}), 404
            if inst not in admin.instituicoes:
                return jsonify({'erro': 'Admin não vinculado a essa instituição.'}), 403
            return jsonify({'token': inst.token}), 200
        return jsonify({'erro': 'admin_id é necessário para acessar o token.'}), 400

    @app.route('/api/instituicoes/join_by_token', methods=['POST'])
    def join_by_token():
        ''' Vincula um usuário ou admin a uma instituição via token da instituição '''
        data = request.get_json()
        token = data.get('token')
        user_id = data.get('user_id')
        admin_id = data.get('admin_id')
        role = data.get('role', 'user')

        if not token or (not user_id and not admin_id):
            return jsonify({'erro': 'token e user_id/admin_id são necessários.'}), 400

        inst = Instituicao.query.filter_by(token=token).first()
        if not inst:
            return jsonify({'erro': 'Token inválido.'}), 404

        if role == 'admin' and admin_id:
            admin = Admin.query.get(admin_id)
            if not admin:
                return jsonify({'erro': 'Admin não encontrado.'}), 404
            if inst in admin.instituicoes:
                return jsonify({'mensagem': 'Admin já vinculado a essa instituição.'}), 200
            admin.instituicoes.append(inst)
            admin.active_inst_id = inst.id
            db.session.commit()
            return jsonify({'mensagem': f'Admin vinculado à instituição {inst.nome}', 'instituicao': inst.to_dict()}), 200

        if role == 'user' and user_id:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'erro': 'User não encontrado.'}), 404
            if inst in user.instituicoes:
                return jsonify({'mensagem': 'Usuário já vinculado a essa instituição.'}), 200
            user.instituicoes.append(inst)
            user.active_inst_id = inst.id
            db.session.commit()
            return jsonify({'mensagem': f'Usuário vinculado à instituição {inst.nome}', 'instituicao': inst.to_dict()}), 200

        return jsonify({'erro': 'Dados inválidos.'}), 400

    @app.route('/api/instituicoes/vincular', methods=['POST'])
    def vincular_instituicao():
        ''' Vincula um admin a uma instituição existente '''
        data = request.get_json()
        admin_id = data.get('admin_id')
        inst_id = data.get('inst_id')
        admin = Admin.query.get(admin_id)
        inst = Instituicao.query.get(inst_id)
        if not admin or not inst:
            return jsonify({'erro': 'Admin ou instituição não encontrados.'}), 404
        if inst in admin.instituicoes:
            return jsonify({'mensagem': 'Admin já vinculado.'}), 200
        admin.instituicoes.append(inst)
        admin.active_inst_id = inst.id
        db.session.commit()
        return jsonify({'mensagem': f'{admin.nome} vinculado à instituição {inst.nome}.'}), 200


    # --- API: ESPAÇOS ---
    @app.route('/api/espacos', methods=['GET'])
    def get_espacos():
        ''' Lista todos os espaços ou filtra por instituição '''
        inst_id = request.args.get('inst_id', type=int)
        query = Espaco.query
        if inst_id:
            query = query.filter_by(id_inst=inst_id)
        espacos = query.all()
        return jsonify([e.to_dict() for e in espacos]), 200

    @app.route('/api/espacos', methods=['POST'])
    def create_espaco():
        ''' Cria um novo espaço '''
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
        ''' Atualiza os detalhes de um espaço '''
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
        ''' Deleta um espaço '''
        espaco = Espaco.query.get_or_404(id)
        db.session.delete(espaco)
        db.session.commit()
        return jsonify({'message': 'Espaço deletado com sucesso.'}), 200

    @app.route('/api/espacos/<int:espaco_id>/horarios_disponiveis', methods=['GET'])
    def get_horarios_disponiveis(espaco_id):
        ''' Retorna os horários disponíveis para um espaço em uma data específica '''
        data_str = request.args.get('data')
        if not data_str:
            return jsonify({'erro': 'A data é obrigatória'}), 400
        try:
            data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD.'}), 400

        espaco = Espaco.query.get_or_404(espaco_id)
        todos_slots = gerar_slots(espaco.duracao_padrao)
        reservas_no_dia = Reserva.query.filter_by(id_espaco=espaco_id, data_reserva=data_obj).all()
        horarios_reservados = {(r.hora_inicio, r.hora_fim) for r in reservas_no_dia}
        slots_disponiveis = [
            {'inicio': inicio.strftime('%H:%M'), 'fim': fim.strftime('%H:%M')}
            for inicio, fim in todos_slots
            if not any(inicio < r_fim and fim > r_inicio for r_inicio, r_fim in horarios_reservados)
        ]
        return jsonify(slots_disponiveis)


    # --- API: AUTENTICAÇÃO ---
    @app.route('/api/register/user', methods=['POST'])
    def register_user():
        ''' Cria um novo usuário '''
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
        token = data.get('token')
        inst_id = data.get('inst_id')
        if token:
            inst = Instituicao.query.filter_by(token=token).first()
            if inst:
                new_user.instituicoes.append(inst)
                new_user.active_inst_id = inst.id
        elif inst_id:
            inst = Instituicao.query.get(inst_id)
            if inst:
                new_user.instituicoes.append(inst)
                new_user.active_inst_id = inst.id
        db.session.commit()
        return jsonify({'message': 'Usuário criado com sucesso!', 'user': new_user.to_dict()}), 201

    @app.route('/api/register/admin', methods=['POST'])
    def register_admin():
        ''' Cria um novo administrador '''
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
        token = data.get('token')
        inst_id = data.get('inst_id')
        if token:
            inst = Instituicao.query.filter_by(token=token).first()
            if inst:
                new_admin.instituicoes.append(inst)
                new_admin.active_inst_id = inst.id
        elif inst_id:
            inst = Instituicao.query.get(inst_id)
            if inst:
                new_admin.instituicoes.append(inst)
                new_admin.active_inst_id = inst.id
        db.session.commit()
        return jsonify({'message': 'Administrador criado com sucesso!','admin': new_admin.to_dict()}), 201

    @app.route('/api/login', methods=['POST'])
    def login():
        ''' Autentica um usuário ou admin e retorna seus dados '''
        data = request.get_json()
        if not data or not data.get('email') or not data.get('senha'):
            abort(400, description="E-mail ou senha não fornecidos.")
        user = User.query.filter_by(email=data['email']).first()
        if user and check_password_hash(user.senha, data['senha']):
            return jsonify({
                "status": "success",
                "user_type": "user",
                "user_data": user.to_dict(),
                "instituicoes": [i.to_dict() for i in user.instituicoes]
            }), 200
        admin = Admin.query.filter_by(email=data['email']).first()
        if admin and check_password_hash(admin.senha, data['senha']):
            return jsonify({
                "status": "success",
                "user_type": "admin",
                "user_data": admin.to_dict(),
                "instituicoes": [i.to_dict() for i in admin.instituicoes]
            }), 200
        return jsonify({"status": "error", "message": "Credenciais inválidas."}), 401

    # --- API: RESERVAS ---
    @app.route('/api/reservas', methods=['GET'])
    def listar_reservas():
        ''' Lista todas as reservas ou filtra por instituição '''
        inst_id = request.args.get('inst_id', type=int)
        query = Reserva.query
        if inst_id:
            query = query.join(Espaco).filter(Espaco.id_inst == inst_id)
        reservas = query.all()
        return jsonify([r.to_dict_history() for r in reservas]), 200

    @app.route('/api/reservas', methods=['POST'])
    def criar_reserva():
        ''' Cria uma nova reserva '''
        data = request.get_json()
        id_espaco = data.get('id_espaco')
        user_email = data.get('user_email')
        data_reserva = data.get('data_reserva')
        hora_inicio = data.get('hora_inicio')
        observacoes = data.get('observacoes', '')

        if not all([id_espaco, user_email, data_reserva, hora_inicio]):
            return jsonify({'erro':'Dados insuficientes'}), 400

        user = User.query.filter_by(email=user_email).first()
        if not user:
            return jsonify({'erro':'Usuário não encontrado'}), 404

        esp = Espaco.query.get(id_espaco)
        if not esp:
            return jsonify({'erro':'Espaço não encontrado'}), 404

        try:
            data_obj = datetime.fromisoformat(data_reserva).date()
            hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M').time()
            dur = esp.duracao_padrao
            hora_fim_dt = (datetime.combine(data_obj, hora_inicio_obj) + timedelta(minutes=dur)).time()
        except Exception as e:
            return jsonify({'erro':'Formato de data/hora inválido', 'detalhe': str(e)}), 400

        # Verificação de conflito
        conflito = Reserva.query.filter(
            Reserva.id_espaco == id_espaco,
            Reserva.data_reserva == data_obj,
            Reserva.hora_inicio < hora_fim_dt,
            Reserva.hora_fim > hora_inicio_obj
        ).first()
        if conflito and not esp.multi_reservas:
            return jsonify({'erro': 'Este horário já está reservado.'}), 409

        reserva = Reserva(id_espaco=id_espaco, id_user=user.id, data_reserva=data_obj, hora_inicio=hora_inicio_obj, hora_fim=hora_fim_dt, observacoes=observacoes)
        db.session.add(reserva)
        db.session.commit()
        return jsonify({'mensagem':'Reserva criada com sucesso'}), 201

    return app
