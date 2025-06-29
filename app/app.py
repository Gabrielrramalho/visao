from flask import Flask, render_template, request, redirect, url_for, flash

from datetime import datetime
from models import db, Aluno, Exame, Escola
from sqlalchemy.orm import joinedload

app = Flask(__name__)

app.secret_key = 'secretkey'

# Ajuste a URI conforme seu banco de dados (SQLite por padrão)
app.config.update(
    SQLALCHEMY_DATABASE_URI=
    'postgresql+psycopg2://meu_usuario:minha_senha@localhost:5432/postgres',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        'pool_pre_ping': True,  # verifica se a conexão está viva antes de usar
        'pool_recycle':
        280,  # recicla conexões que ficaram muito tempo ociosas
    })
db.init_app(app)
# --------------------
# ROTAS
# --------------------


@app.route("/")
def index():
    # 2) Verifica se veio "aluno_id" na query string
    aluno_id = request.args.get("aluno_id", type=int)
    aluno = None
    if aluno_id:
        aluno = Aluno.query.get(aluno_id)

    # 3) Passa "aluno" para o template, junto com "escolas"
    return render_template("index.html", aluno=aluno)


@app.route("/landing")
def landing():
    # Se o seu arquivo se chama landin.html:
    return render_template("landin.html")

@app.route('/exames')
def lista_exames():
    exames = (Exame.query.options(
        joinedload(Exame.aluno).joinedload(Aluno.escola)).order_by(
            Exame.data_hora_escaneamento.desc()).all())
    return render_template('exames.html', exames=exames)


@app.route('/exames/excluir/<int:id>', methods=['POST'])
def excluir_exame(id):
    exame = Exame.query.get_or_404(id)
    db.session.delete(exame)
    db.session.commit()
    flash('Exame excluído.', 'info')
    return redirect(url_for('lista_exames'))


@app.route('/exames/editar/<int:id>', methods=['GET', 'POST'])
def editar_exame(id):
    exame = Exame.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # 1) Data/Hora do exame
            data_hora_raw = request.form.get('InputDataHoraEscaneamento', '')
            exame.data_hora_escaneamento = (datetime.strptime(
                data_hora_raw, '%Y-%m-%dT%H:%M') if data_hora_raw else None)

            # 2) ID do aluno (name="id_aluno" no form)
            aluno_id_raw = request.form.get('id_aluno', '')
            exame.id_aluno = int(aluno_id_raw) if aluno_id_raw else None

            # 3) Campos OD (olho direito) – conversões para float/int
            raio_od = request.form.get('raio_corneano_od_mm', '')
            exame.raio_corneano_od_mm = float(raio_od) if raio_od else None

            steeper_od = request.form.get('eixo_querato_steeper_od', '')
            exame.eixo_querato_steeper_od = float(
                steeper_od) if steeper_od else None

            flatter_od = request.form.get('eixo_querato_flatter_od', '')
            exame.eixo_querato_flatter_od = float(
                flatter_od) if flatter_od else None

            se_od = request.form.get('SE_Direito', '')
            exame.se_direito = float(se_od) if se_od else None

            ds_od = request.form.get('DS_Direito', '')
            exame.ds_direito = float(ds_od) if ds_od else None

            dc_od = request.form.get('DC_Direito', '')
            exame.dc_direito = float(dc_od) if dc_od else None

            axis_od = request.form.get('Axis_Direito', '')
            exame.axis_direito = int(axis_od) if axis_od else None

            # 4) Distância interpupilar
            dip = request.form.get('distancia_interpupilar_mm', '')
            exame.distancia_interpupilar_mm = float(dip) if dip else None

            # 5) Campos OS (olho esquerdo)
            se_os = request.form.get('SE_Esquerdo', '')
            exame.se_esquerdo = float(se_os) if se_os else None

            ds_os = request.form.get('DS_Esquerdo', '')
            exame.ds_esquerdo = float(ds_os) if ds_os else None

            dc_os = request.form.get('DC_Esquerdo', '')
            exame.dc_esquerdo = float(dc_os) if dc_os else None

            axis_os = request.form.get('Axis_Esquerdo', '')
            exame.axis_esquerdo = int(axis_os) if axis_os else None

            raio_os = request.form.get('raio_corneano_os_mm', '')
            exame.raio_corneano_os_mm = float(raio_os) if raio_os else None

            steeper_os = request.form.get('eixo_querato_steeper_os', '')
            exame.eixo_querato_steeper_os = float(
                steeper_os) if steeper_os else None

            flatter_os = request.form.get('eixo_querato_flatter_os', '')
            exame.eixo_querato_flatter_os = float(
                flatter_os) if flatter_os else None

            # Atualiza o registro
            db.session.commit()

            flash('Exame atualizado com sucesso!', 'success')
            return redirect(url_for('lista_exames'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar exame: {e}', 'danger')
            return redirect(request.url)

    # GET: renderiza o formulário já com os valores de 'exame'
    return render_template('editar.html', exame=exame)


@app.route('/form-user')
def form_user():
    # GET: busca dados para popular selects
    escolas = Escola.query.order_by(Escola.nome).all()
    regioes = [f"{i:02d}" for i in range(1, 33)]
    return render_template("form_user.html", escolas=escolas, regioes=regioes)


@app.route("/aluno", methods=["GET", "POST"])
def form_aluno():
    if request.method == "POST":
        # 1) coleta dados do form
        nome_raw = request.form.get("nome", "").strip()
        nasc_raw = request.form.get("data_nascimento", "")
        sexo = request.form.get("sexo", "")
        id_esc_raw = request.form.get("id_escola", "")
        regiao = request.form.get("regiao_administrativa", "")

        # 2) validações básicas
        if not nome_raw or not nasc_raw or not sexo or not id_esc_raw or not regiao:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return redirect(url_for("form_aluno"))

        # converte data
        try:
            data_nascimento = datetime.strptime(nasc_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("Data de nascimento inválida.", "danger")
            return redirect(url_for("form_aluno"))

        # converte escola
        try:
            id_escola = int(id_esc_raw)
        except ValueError:
            flash("Escola inválida.", "danger")
            return redirect(url_for("form_aluno"))

        # 3) cria instância e persiste
        aluno = Aluno(nome=nome_raw,
                      data_nascimento=data_nascimento,
                      sexo=sexo,
                      id_escola=id_escola,
                      regiao_administrativa=regiao)
        db.session.add(aluno)
        db.session.commit()

        flash("Aluno cadastrado com sucesso!", "success")
        aluno = Aluno.query.order_by(Aluno.id_aluno.desc()).first()
        print(aluno.id_aluno)
        return redirect(url_for("index", aluno_id=aluno.id_aluno))


@app.route('/escola', methods=['GET', 'POST'])
def form_escola():
    if request.method == 'POST':
        # 1) Pega todos os campos do form
        nome = request.form['nome']
        logradouro = request.form['logradouro']
        numero = request.form['numero']
        complemento = request.form.get('complemento') or None
        bairro = request.form['bairro']
        cidade = request.form['cidade']
        estado = request.form['estado']
        cep = request.form['cep']
        regiao = request.form['regiao_administrativa']
        # latitude/longitude são opcionais
        lat_raw = request.form.get('latitude')
        lon_raw = request.form.get('longitude')
        latitude = float(lat_raw) if lat_raw else None
        longitude = float(lon_raw) if lon_raw else None

        # 2) Cria a instância do modelo
        escola = Escola(nome=nome,
                        logradouro=logradouro,
                        numero=numero,
                        complemento=complemento,
                        bairro=bairro,
                        cidade=cidade,
                        estado=estado,
                        cep=cep,
                        regiao_administrativa=regiao,
                        latitude=latitude,
                        longitude=longitude)

        # 3) Persiste no banco
        db.session.add(escola)
        db.session.commit()

        flash('Escola cadastrada com sucesso!', 'success')
        # redireciona para a listagem ou para o próprio form
        return redirect(url_for('form_escola'))

    # método GET: renderiza o template do formulário
    return render_template('form_escola.html')


@app.route('/formulario', methods=['POST'])
def process_form():

    data_hora_raw = request.form[
        'InputDataHoraEscaneamento']  # formato 'YYYY-MM-DDTHH:MM'
    data_hora_exame = datetime.strptime(data_hora_raw, '%Y-%m-%dT%H:%M') \
                      if data_hora_raw else None

    # 2) OD (olho direito)
    # Estes campos vêm dos inputs dentro da coluna id="primeira" e da coluna id="segunda"
    od_input1 = request.form.get(
        'raio_corneano_od_mm')  # Ex.: alguma medida (depende do modelo)
    od_input2 = request.form.get(
        'eixo_querato_steeper_od')  # Ex.: outra medida
    od_input3 = request.form.get(
        'eixo_querato_flatter_od')  # Ex.: terceira medida
    od_se = request.form.get('Input9')  # placeholder="SE"
    od_ds = request.form.get('DS_Direito')
    od_dc = request.form.get('DC_Direito')  # placeholder="DS"
    od_axis = request.form.get('Axis_Direito')  # placeholder="Axis"

    # 3) OS (olho esquerdo)
    os_input4 = request.form.get(
        'distancia_interpupilar_mm')  # Ex.: alguma medida
    os_input5 = request.form.get('Input5')  # Ex.: outra medida
    os_se = request.form.get('SE_Esquerdo')  # placeholder="SE"
    os_ds = request.form.get('DS_Esquerdo')  # placeholder="DS"
    os_dc = request.form.get('DC_Esquerdo')  # placeholder="DC"
    os_axis = request.form.get('Axis_Esquerdo')  # placeholder="Axis"
    os_input6 = request.form.get(
        'raio_corneano_os_mm')  # Ex.: medida complementar
    os_input7 = request.form.get(
        'eixo_querato_steeper_os')  # Ex.: medida complementar
    os_input8 = request.form.get(
        'eixo_querato_flatter_os')  # Ex.: medida complementar
    aluno_id_raw = request.form.get("aluno_id", "")
    print(aluno_id_raw)
    try:
        aluno_id = int(aluno_id_raw) if aluno_id_raw else None
    except ValueError:
        aluno_id = None

    # Se não vier aluno_id, dispense ou trate como quiser:
    if not aluno_id:
        flash("ID do aluno não encontrado.", "danger")
        return redirect(url_for("index"))

    aluno = Aluno.query.get(aluno_id)
    if not aluno:
        flash("Aluno não existe.", "danger")
        return redirect(url_for("index"))

    # 4) Criação do objeto e inserção no banco
    # Nota: o modelo Exame deve ter colunas/membros que correspondam exatamente
    # aos atributos usados abaixo. Ajuste nomes de atributos conforme seu modelo.
    exame = Exame(data_hora_escaneamento=data_hora_exame,
                  id_aluno=aluno_id,
                  raio_corneano_od_mm=od_input1,
                  eixo_querato_steeper_od=od_input2,
                  eixo_querato_flatter_od=od_input3,
                  se_direito=od_se,
                  ds_direito=od_ds,
                  dc_direito=od_dc,
                  axis_direito=od_axis,
                  distancia_interpupilar_mm=os_input4,
                  input5=os_input5,
                  se_esquerdo=os_se,
                  ds_esquerdo=os_ds,
                  dc_esquerdo=os_dc,
                  axis_esquerdo=os_axis,
                  raio_corneano_os_mm=os_input6,
                  eixo_querato_steeper_os=os_input7,
                  eixo_querato_flatter_os=os_input8)

    db.session.add(exame)
    db.session.commit()

    return redirect(url_for('lista_exames'))


# Rota para fornecer dados
@app.route('/api/data', methods=['GET'])
def streamlit_dashboard():
    return redirect("http://localhost:8501", code=302)


with app.app_context():
    db.create_all()
    print("Banco de dados e tabelas criados com sucesso.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
