import os, json
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
USER_DB = 'users.json'
UPLOAD_BASE = 'static/uploads'

os.makedirs(UPLOAD_BASE, exist_ok=True)
if not os.path.exists(USER_DB):
    with open(USER_DB, 'w') as f:
        json.dump({}, f)

def load_users():
    try:
        with open(USER_DB, 'r') as f:
            return json.load(f)
    except:
        with open(USER_DB, 'w') as f:
            json.dump({}, f)
        return {}

def save_users(users):
    with open(USER_DB, 'w') as f:
        json.dump(users, f, indent=2)

def get_user_paths(username):
    base = os.path.join(UPLOAD_BASE, username)
    photo_dir = os.path.join(base, 'photos')
    trash_dir = os.path.join(base, 'trash')
    os.makedirs(photo_dir, exist_ok=True)
    os.makedirs(trash_dir, exist_ok=True)
    return base, photo_dir, trash_dir

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return "User exists!"
        users[username] = generate_password_hash(password)
        save_users(users)
        get_user_paths(username)
        return redirect('/')
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    users = load_users()
    username = request.form['username']
    password = request.form['password']
    if username in users and check_password_hash(users[username], password):
        session['username'] = username
        return redirect('/photosave')
    return "❌ Invalid login"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/photosave', methods=['GET', 'POST'])
def photosave():
    if 'username' not in session: return redirect('/')
    username = session['username']
    _, photo_dir, _ = get_user_paths(username)

    if request.method == 'POST':
        file = request.files.get('photo')
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(photo_dir, filename))
            return redirect('/photosave')

    photos = os.listdir(photo_dir)
    return render_template('photosave.html', photos=photos, username=username)

@app.route('/download/<filename>')
def download(filename):
    if 'username' not in session: return redirect('/')
    _, photo_dir, _ = get_user_paths(session['username'])
    return send_from_directory(photo_dir, filename, as_attachment=True)

@app.route('/delete/<filename>')
def delete(filename):
    if 'username' not in session: return redirect('/')
    _, photo_dir, trash_dir = get_user_paths(session['username'])
    src = os.path.join(photo_dir, filename)
    dst = os.path.join(trash_dir, filename)
    if os.path.exists(src):
        os.rename(src, dst)
    return redirect('/photosave')

@app.route('/trash')
def trash():
    if 'username' not in session: return redirect('/')
    _, _, trash_dir = get_user_paths(session['username'])
    photos = os.listdir(trash_dir)
    return render_template('trash.html', photos=photos, username=session['username'])

@app.route('/restore/<filename>')
def restore(filename):
    if 'username' not in session: return redirect('/')
    _, photo_dir, trash_dir = get_user_paths(session['username'])
    src = os.path.join(trash_dir, filename)
    dst = os.path.join(photo_dir, filename)
    if os.path.exists(src):
        os.rename(src, dst)
    return redirect('/trash')

@app.route('/permanent_delete/<filename>')
def permanent_delete(filename):
    if 'username' not in session: return redirect('/')
    _, _, trash_dir = get_user_paths(session['username'])
    path = os.path.join(trash_dir, filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect('/trash')

@app.route('/profile')
def profile():
    if 'username' not in session: return redirect('/')
    username = session['username']
    _, photo_dir, trash_dir = get_user_paths(username)
    photo_count = len(os.listdir(photo_dir))
    trash_count = len(os.listdir(trash_dir))
    return render_template('profile.html', username=username, photos=photo_count, trash=trash_count)

if __name__ == '__main__':
    app.run(debug=True)
