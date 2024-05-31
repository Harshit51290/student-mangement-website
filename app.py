import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def init_sqlite_db():
    if not os.path.exists('user_databases'):
        os.makedirs('user_databases')
    conn = sqlite3.connect('students.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
    conn.close()

init_sqlite_db()

def create_user_database(username):
    db_path = f'user_databases/{username}.db'
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, grade TEXT)')
    conn.close()
    return db_path

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            with sqlite3.connect('students.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                con.commit()
                create_user_database(username)
                flash("User successfully registered.", "success")
                return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose a different one.", "error")
        except Exception as e:
            flash(f"Error occurred: {e}", "error")
    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('students.db') as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cur.fetchone()

            if user and check_password_hash(user[2], password):
                session['username'] = username
                session['db_path'] = f'user_databases/{username}.db'
                return redirect(url_for('home'))
            else:
                flash("Invalid username or password.", "error")
                return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout/')
def logout():
    session.pop('username', None)
    session.pop('db_path', None)
    return redirect(url_for('login'))

@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'handle_404']
    if 'username' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/add-student/', methods=['POST'])
def add_student():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        name = request.form['name']
        age = request.form['age']
        grade = request.form['grade']

        with sqlite3.connect(session['db_path']) as con:
            cur = con.cursor()
            cur.execute("INSERT INTO students (name, age, grade) VALUES (?, ?, ?)", (name, age, grade))
            con.commit()
            msg = "Student successfully added."
    except Exception as e:
        msg = f"Error occurred: {e}"
    finally:
        return jsonify(msg=msg)


@app.route('/view-students/', methods=['GET'])
def view_students():
    if 'username' not in session:
        return redirect(url_for('login'))
    students = []
    try:
        with sqlite3.connect(session['db_path']) as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM students")
            students = cur.fetchall()
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        return jsonify(students=students)

@app.route('/update-student/', methods=['POST'])
def update_student():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        student_id = request.form['id']
        name = request.form['name']
        age = request.form['age']
        grade = request.form['grade']

        with sqlite3.connect(session['db_path']) as con:
            cur = con.cursor()
            cur.execute("UPDATE students SET name = ?, age = ?, grade = ? WHERE id = ?", (name, age, grade, student_id))
            con.commit()
            msg = "Student successfully updated."
    except Exception as e:
        msg = f"Error occurred: {e}"
    finally:
        return jsonify(msg=msg)

@app.route('/delete-student/', methods=['POST'])
def delete_student():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        student_id = request.form['id']

        with sqlite3.connect(session['db_path']) as con:
            cur = con.cursor()
            cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
            con.commit()
            msg = "Student successfully deleted."
    except Exception as e:
        msg = f"Error occurred: {e}"
    finally:
        return jsonify(msg=msg)

@app.errorhandler(404)
def handle_404(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
