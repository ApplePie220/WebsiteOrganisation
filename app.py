from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g
from config import host, user, password, db_name
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
    return render_template('page404.html', title='Страница не найдена', menu=getMenu())

@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated: #если юзер уже авторизован, то при переходе на авторизацию
        return redirect(url_for('profile')) # его будет перенаправлять в его профиль
    user = None
    if request.method == "POST":
        user_login = request.form.get('username')
        enter_pass = request.form.get('psw')
        if user_login and enter_pass:
            db = connection_db(user_log="postgres", user_pass="frerard2203")
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
        db = connection_db("postgres", "frerard2203")
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
    db = connection_db("postgres", "frerard2203")
    with db:
        print("получаем клиентов")
    return render_template('clients_list.html', menu=getMenu(), posts=getClientAnounce(db))

@app.route('/edit-tasks', methods=["POST", "GET"])
@login_required
def addTask():
    if request.method == "POST":
        db = connection_db("postgres", "frerard2203")
        with db:
            if len(request.form['name']) > 0 and len(request.form['post']) > 0:
                res = addtask(request.form['name'], request.form['post'], db)
                if not res:
                    flash('Ошибка добавления региона', category='error')
                else:
                    flash('Регион успешно добавлен', category='succes')
            else:
                flash('Ошибка добавления региона', category='error')
    return render_template('add_task.html', menu=getMenu(), title='Добавление задания')

@app.route('/index')
@login_required

def index():
    if 'current_user' in session:
        user = {'employee_login': session.get('current_user', 'secret')[4]}
        db = connection_db(session.get('current_user', 'secret')[4], session.get('user_password', 'secret'))
        posts=getTaskAnounce(db)
        with db:
            print("главная")
    return render_template('index.html', menu=getMenu(), posts=posts)

@app.route('/task/<int:id_task>')
@login_required
def showTask(id_task):
    db = connection_db("postgres", "frerard2203")
    with db:
        id, desc = getTask(id_task, db)
        if not id:
            abort(404)

    return render_template('task.html', menu=getMenu(), title=id, post=desc)

@app.route('/client/<int:id_client>')
@login_required
def showClient(id_client):
    db = connection_db("postgres", "frerard2203")
    with db:
        id, lastn = getClient(id_client, db)
        if not id:
            abort(404)

    return render_template('client.html', menu=getMenu(), title=id, post=lastn)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    return render_template("profile.html", menu=getMenu(), title="Профиль")

@app.route('/about')
@login_required
def about():
    print(url_for('about'))
    return render_template('about.html', title="Stray Parents", menu=getMenu())

@app.route('/adminka', methods=["POST", "GET"])
@login_required
def adminka():
    if request.method == "POST":
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Критиническая ошибка отправки.', category='error')
        print(request.form)
    return render_template('adm.html', title='Оставьте свой отзыв, мы его даже не запишем!', menu=getMenu())

def close_db(error):
    # закрываем соединение с бд
    if hasattr(g, 'link_db'):
        g.link_db.close( )
        print("PostgreSQL connected closed")


if __name__ == '__main__':
    app.run()
