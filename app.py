from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g
from FDataBase import *
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
import psycopg2

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

login_manager = LoginManager(app)
login_manager.session_protection = "strong"
login_manager.login_view = 'login'
login_manager.login_message = "Пожалуйста, авторизуйтесь  для доступа к закрытым страницам"
login_manager.login_message_category = "success"
user_is_manager = False

def connection_db(user_log, user_pass):
    try:
        # подключаемся к бд
        connection = psycopg2.connect(
            host='localhost',
            user=user_log,
            password=user_pass,
            database='organisdb'
        )
        connection.autocommit = True
        print("PostgreSQL connected")
        return connection

    except Exception as _ex:
        print("ERROR while working with PostgreSQL", _ex)
        return False


@login_manager.user_loader
def load_user(user_id):
     db = connection_db(session.get('current_user', 'secret')[4], session.get('user_password', 'secret'))
     return UserLogin().from_DB(user_id,db)

@app.errorhandler(404)
def pageNotFound(error):
    return render_template('page404.html', title='Страница не найдена', menu=getMenu(), manager=user_is_manager)

@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated: #если юзер уже авторизован, то при переходе на авторизацию
        return redirect(url_for('profile')) # его будет перенаправлять в его профиль
    user = None
    if request.method == "POST":
        user_login = request.form.get('username')
        enter_pass = request.form.get('psw')
        if user_login and enter_pass:
            db = connection_db(user_log="postgres", user_pass="74NDF*305c")
            with db:
                user_password_correct = getPassUserByLogin(user_login, enter_pass, db)
                if user_password_correct:
                    user = getUserByLogin(user_login, db)
                    userlogin = UserLogin().create(user)
                    rm = True if request.form.get('remainme') else False
                    login_user(userlogin, remember=rm)
                    session['current_user'] = user
                    session['user_password'] = enter_pass
                    return redirect(request.args.get("next") or url_for("profile"))
                else:
                    flash("Введен неверный пароль.", "error")

        else:
            flash('Неверный ввод логина/пароля', 'error')
    # else:
        # if 'current_user' in session:
        #     db = connection_db(session.get('current_user', 'secret')[4], session.get('user_password', 'secret'))
        #     user['employee_login'] = session.get('current_user', 'secret')[4]
        #     print(session.get('current_user', 'secret')[4], session.get('user_password', 'secret'))

    return render_template("login.html", menu = getMenu(), title="Авторизация")

@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        db = connection_db("postgres", "74NDF*305c")
        with db:
            if len(request.form['name']) > 0 and len(request.form['username']) > 0 \
                and len(request.form['psw']) > 3 and request.form['psw'] == request.form['psw2']:
                    res = addUser(request.form['name'],request.form['username'],
                    request.form['psw'], request.form['phone'],request.form['email'],request.form['role'], db)
                    if res:
                        flash('Вы успешно зарегистрированы.', 'success')
                        return redirect(url_for('login'))
                    else:
                        flash('Ошибка при Добавлении в бд', 'error')
            else:
                flash('Неверно заполнены поля', 'error')

    return render_template('register.html', menu=getMenu(), title="Регистрация")

@app.route('/clients')
@login_required
def clients():
    db = connection_db("postgres", "74NDF*305c")
    position_user = getPositionUser(session.get('current_user', 'secret')[0], db)
    user_is_manager = True if position_user == 1 else False
    with db:
        print("получаем клиентов")
    return render_template('clients_list.html', menu=getMenu(), posts=getClientAnounce(db), manager=user_is_manager)

@app.route('/add-tasks', methods=["POST", "GET"])
@login_required
def addTask():
    if 'current_user' in session:
        db = connection_db(session.get('current_user', 'secret')[4], session.get('user_password', 'secret'))
        user = {'employee_login': session.get('current_user', 'secret')[4]}
        position_user = getPositionUser(session.get('current_user', 'secret')[0], db)
        user_is_manager = True if position_user == 1 else False
    if request.method == "POST":
        with db:
                status = request.form.get('status')
                contract = request.form.get('contract')
                executor = request.form.get('executor')
                client = request.form.get('client')
                priority = request.form.get('priority')
                author = session.get('current_user', 'secret')[0]
                if not (status or contract or executor or client or priority or author):
                    flash("Заполните все поля", "error")
                else:
                    res = addtask(status,contract,author,executor,client,priority, db)
                    if not res:
                        flash('Ошибка добавления задания', category='error')
                    else:
                        flash('Задание успешно добавлено', category='succes')
                return redirect(url_for('index'))
    return render_template('add_task.html', menu=getMenu(), title='Добавление задания', manager =user_is_manager)

@app.route('/index')
@login_required
def index():
    if 'current_user' in session:
        user = {'employee_login': session.get('current_user', 'secret')[4]}
        db = connection_db(session.get('current_user', 'secret')[4], session.get('user_password', 'secret'))
        posts=getTaskAnounce(db)
        position_user = getPositionUser(session.get('current_user', 'secret')[0], db)
        user_is_manager = True if position_user == 1 else False
        with db:
            print("главная")
    return render_template('index.html', menu=getMenu(), posts=posts, manager=user_is_manager)

@app.route('/task/<int:id_task>', methods=['GET', 'POST'])
@login_required
def editTask(id_task):
    task = None
    user = None
    if 'current_user' in session:
        user = {'employee_login': session.get('current_user', 'secret')[4]}
        db = connection_db(session.get('current_user', 'secret')[4], session.get('user_password', 'secret'))
        position_user = getPositionUser(session.get('current_user', 'secret')[0], db)
        user_is_manager = True if position_user == 1 else False
        if request.method == "POST":
            with db:
                status = request.form.get('status')
                executor = request.form.get('executor')
                priority = request.form.get('priority')
                deadline_date = 'null' if  request.form.get('deadline') == 'None' else \
                    request.form.get('deadline')
                acception_date = 'null' if  request.form.get('accept') == 'None' else \
                    request.form.get('accept')
                if not(status or executor or priority or deadline_date or acception_date):
                    flash("Заполните все поля", "error")
                else:
                    updateTask(status, executor,priority,deadline_date,acception_date, id_task)
        else:
            with db:
                task = getTask(id_task, db)
                return redirect(url_for('showTask', id_task=id_task))
    return render_template('edit-task.html',menu=getMenu(), task=task, manager =user_is_manager )


@app.route('/task/<int:id_task>')
def showTask(id_task):
    task = None
    user = None
    if 'current_user' in session:
        user = {'employee_login': session.get('current_user', 'secret')[4]}
        db = connection_db(session.get('current_user', 'secret')[4], session.get('user_password', 'secret'))
        with db:
            task = getTask(id_task,db)
    return render_template('task.html',menu=getMenu(), manager=user_is_manager,task=task)


@app.route('/client/<int:id_client>')
@login_required
def showClient(id_client):
    db = connection_db("postgres", "74NDF*305c")
    position_user = getPositionUser(session.get('current_user', 'secret')[0], db)
    user_is_manager = True if position_user == 1 else False
    with db:
        id, lastn = getClient(id_client, db)
        if not id:
            abort(404)

    return render_template('client.html', menu=getMenu(), title=id, post=lastn, manager=user_is_manager)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    db = connection_db(session.get('current_user', 'secret')[4], session.get('user_password', 'secret'))
    position_user = getPositionUser(session.get('current_user', 'secret')[0], db)
    user_is_manager = True if position_user == 1 else False
    return render_template("profile.html", menu=getMenu(), title="Профиль", manager=user_is_manager)

# def close_db(error):
#     # закрываем соединение с бд
#     if hasattr(g, 'link_db'):
#         g.link_db.close( )
#         print("PostgreSQL connected closed")


if __name__ == '__main__':
    app.run()
