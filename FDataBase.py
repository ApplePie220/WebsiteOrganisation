import math
import time
import psycopg2
from flask import session
from psycopg2.extras import DictCursor

def getMenu():
    menu = [{"name": "Список заданий", "url": "allowed-information"},
            {"name": "Редактор заданий", "url": "edit-tasks"},
            {"name": "Отзыв", "url": "adminka"},
            {"name": "Список клиентов", "url": "clients-list"},
            {"name": "Авторизация", "url": "login"}]
    return menu

def getTaskAnounce(db):
    try:
            with db.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT * FROM task ORDER BY task_number")
                res = cursor.fetchall()
                if res:
                    return res
    except Exception as e:
        print(e)
        print("Ошибка в получении заданий.")

    return []


def getClientAnounce(db):
    try:
            with db.cursor(cursor_factory=DictCursor) as cursor:

                cursor.execute("SELECT * FROM client ORDER BY client_number")
                res = cursor.fetchall()
                if res: return res
    except Exception as e:
        print(e)
        print("Ошибка в получении клиентов.")

    return []

def addtask(status,contract,author,executor,client,priority, db):
    try:
            with db.cursor() as cursor:
                cursor.execute("CALL add_task(%s,%s,%s,%s,%s,%s)", (status,contract,author,client,executor,priority))
                #db.commit()
    except Exception as e:
        print("Ошибкад добавления задачи " + e)
        return False

    return True

def getTask(id, db):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM task WHERE task_number =%(task_number)s",
                           {'task_number':id})
            res = cursor.fetchone()
            if res:
                return res
    except Exception as e:
        print(e)
        print("Ошибка получения таска из БД")
    return (False, False)

def updateTask(status, executor,  priority,deadline,acception, db, task_id):
    try:
        with db.cursor() as cursor:
            cursor.execute(f'''UPDATE task SET task_status = '{status}',
                                    executor_number = '{executor}',
                                    task_priority = '{priority}',
                                    deadline_date = '{deadline}',
                                    acception_date = '{acception}'
                                    WHERE task_number = '{task_id}' ''')

    except Exception as e:
        print(e)
        print("Ошибка получения таска из БД")
def getClient(id, db):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT employee_id,last_mame FROM employees WHERE employee_id =%(employee_id)s",
                           {'employee_id':id})
            res = cursor.fetchone()
            if res:
                return res
    except Exception as e:
        print(e)
        print("Ошибка чтения из БД")
    return (False, False)

def addUser(name, login,password,phone,email,role, db ):
    try:
            id_role = 0
            if role == 'worker':
                id_role = 2
            if role == 'manager':
                id_role = 1
            with db.cursor() as cursor:
                cursor.execute("CALL create_user(%s,%s,%s,%s,%s,%s)", (name,email,phone,login,password,id_role))
                db.commit()
    except Exception as e:
        print(e)
        print("Ошибка добавления пользователя в бд")
        return False

    return True


def getUser(user_id, db):
    try:
            with db.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT * FROM employee WHERE employee_number = %(employee_number)s",
                               {'employee_number': user_id})
                res = cursor.fetchone()
                if not res:
                    print("Пользовтель не найден.")
                    return False
                return res
    except Exception as e:
        print(e)
        print("Ошибка получения данных из бд.")
    return False

def getUserByLogin(login, db):
    try:
            with db.cursor(cursor_factory=DictCursor) as cursor:
                try:
                    cursor.execute("SELECT * FROM employee WHERE employee_login = %(employee_login)s",
                                   {'employee_login': login})
                    res = cursor.fetchone()
                except psycopg2.OperationalError as e:
                    print(e)
                    res = False
                #if not res:
                    #print("Пользователь не найден.")
                return res

    except Exception as e:
        print(e)
        print("Ошибка получения пользователя из бд.")

    return False

def getPassUserByLogin(login,pasw, db):
    try:
            with db.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(f'''SELECT employee_password = crypt('{pasw}', employee_password) 
                                FROM employee WHERE employee_login = '{login}' ''')
                res = cursor.fetchone()[0]
                if not res:
                    print("Пользователь не найден.")
                    return False
                return res

    except Exception as e:
        print(e)
        print("Ошибка получения пользователя из бд.")

    return False

def getPositionUser(user_id, db):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT position_id FROM employee WHERE employee_number = %(employee_number)s",
                           {'employee_number': user_id})
            res = cursor.fetchone()[0]
            if not res:
                print("Пользователя с таким id нет.")
                return False
            return res

    except Exception as e:
        print(e)
        print("Ошибка получения юзера из бд.")

    return False