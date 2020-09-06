from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
from models import Building, User, Announcement, UserMessage

app = Flask(__name__)
import string
from sqlalchemy import or_, and_
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import LoginManager, login_user, logout_user, current_user
from flask_mail import Mail, Message
import psycopg2
import random
from werkzeug.security import generate_password_hash, check_password_hash
from sessions import db_session, engine
from time import strftime
import json

db = SQLAlchemy(app)
ma = Marshmallow(app)

#flask login
login_manager = LoginManager()
login_manager.init_app(app)

#flask_mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'nofences1122@gmail.com'
app.config['MAIL_PASSWORD'] = 'Nofences11'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'key'
app.config['SECURITY_RECOVERABLE'] = True


bcrypt = Bcrypt(app)

connection = engine.connect()


# Show messages
def messages(message):
    print(message)
    flash(message)
    return


def generate_password(length=10):
    password_characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(password_characters) for i in range(length))
    return password


@login_manager.user_loader
def load_user(username):
    return db_session.query(User).filter_by(username=username).first()


@app.route('/')
def index():
    return render_template('map_neigh/map.html', name='name')


@app.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = db_session.query(User).filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash ('Niepoprawny login i/lub hasło')
            return redirect(url_for('login'))

        flash ('Zalogowano poprawnie', 'success')
        login_user(user)
        return redirect(url_for('index'))
    return render_template("map_neigh/login.html")


@app.route('/register', methods=['POST', 'GET'], strict_slashes=False)
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("password2")
        email = request.form.get("email")
        district = request.form.get("district")
        address_id = request.form.get("id_address")

        username_check = db_session.query(User.username).filter_by(username=username).scalar()

        if username_check is None:
            if password == confirm:
                secure_password = generate_password_hash(password)
                newUser = User(username=username, password=secure_password, email=email, district=district, address_id=address_id)
                db_session.add(newUser)
                db_session.commit()
                flash("Zarejestrowano pomyślnie", "success")
                return redirect(url_for("index"))
            else:
                flash("Hasła różnią się od siebie", "danger")
                return render_template("map_neigh/register.html")
        else:
            flash("Wprowadzona nazwa użytkownika jest już zajęta", "danger")
            return render_template("map_neigh/register.html")

    return render_template('map_neigh/register.html')


@app.route('/geojson')
def get_json():
    conn = psycopg2.connect("dbname=nofences user=postgres host=localhost password=postgres")
    cur = conn.cursor()
    cur.execute("select json_build_object('type', 'FeatureCollection', 'features', json_agg("
                                "ST_AsGeoJSON(t.*)::json)) "
                                "from buildings as t;")
    result = cur.fetchall()
    cur.close()
    conn.close()
    result_flat = []
    for sublist in result:
        for item in sublist:
            result_flat.append(item)
    return jsonify(result_flat)


@app.route('/json')
def get_ann_json():
    conn = psycopg2.connect("dbname=nofences user=postgres host=localhost password=postgres")
    cur = conn.cursor()
    cur.execute("select json_build_object('id', a.id, 'text', a.text, 'date', a.date, 'price', a.price, "
                "'building_id', a.building_id) from announcements a;")
    result = cur.fetchall()
    cur.close()
    conn.close()
    result_flat = []
    for sublist in result:
        for item in sublist:
            result_flat.append(item)
    return jsonify(result_flat)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile')
def profile_view():
    users = db_session.query(User).all()
    return render_template('map_neigh/profile.html', users=users)


@app.route('/add', methods=['POST', 'GET'])
def add():
    if request.method == 'POST':
        content = request.form.get('content')
        price = float(request.form.get('price'))
        if price <= 0.0:
            price = None
        building_id = current_user.address_id
        newAnnouncement = Announcement(text=content, price=price, building_id=building_id)
        db_session.add(newAnnouncement)
        db_session.commit()
        flash('Dodano ogłoszenie', 'success')
        return redirect(url_for('index'))

    return render_template('map_neigh/add.html')


@app.route('/restore_password', methods=['POST','GET'], strict_slashes=False)
def restore():
    if request.method == 'POST':
        email = request.form.get('email')
        user = db_session.query(User).filter_by(email=email).scalar()

        if user is not None:
            if user.email == email:
                password = generate_password()
                secure_password = generate_password_hash(password)
                user.password = secure_password
                db_session.commit()
                print (password, secure_password)

                msg = Message('Zmiana hasła', sender='nofences1122@gmail.com', recipients=[user.email])
                msg.body = 'Poprosiłeś o wysłanie Tobie nowego hasła, oto ono: ' + password + ' Jeżeli to nie Ty wysłałeś prośbę o nowe hasło, zignoruj ten e-mail'
                mail.send(msg)
                flash('Na podany e-mail wysłano nowe hasło', 'success')
                return redirect(url_for('login'))
            else:
                flash('Nieprawidłowy adres e-mail', 'danger')
                return redirect(url_for('restore'))
        else:
            flash('Nieprawidłowy adres e-mail', 'danger')
            return redirect(url_for('restore'))

    return render_template('map_neigh/restore_password.html')


@app.route('/change_password', methods=['POST', 'GET'], strict_slashes=False)
def change_password():
    if request.method == 'POST':

        password = current_user.password
        check_password = request.form.get('password')

        if check_password_hash(password, check_password):
            new_password = request.form.get('new_password')
            new_password_confirm = request.form.get('new_password_confirm')

            if new_password_confirm == new_password:
                secure_password = generate_password_hash(new_password)
                current_user.password = secure_password
                db_session.commit()
                logout_user()
                return redirect(url_for('login'))
            else:
                flash('Wybrane hasło nie jest takie samo jak w potwierdzeniu hasła', 'danger')
                return redirect(url_for('change_password'))
        else:
            flash('Stare hasło nie jest poprawne')
            return redirect(url_for('change_password'))

    return render_template('map_neigh/change_password.html')


@app.route('/messages_menu', strict_slashes=False)
def messages_menu():
    username = current_user.username
    chats = db_session.query(UserMessage).filter(or_(UserMessage.receiver==username, UserMessage.sender==username)).all()

    chatters_list = []
    for chat in chats:
        if username == chat.receiver:
            chatter = chat.sender
        else:
            chatter = chat.receiver

        if chatter not in chatters_list:
            chatters_list.append(chatter)

    last_messages = {}
    for chatter in chatters_list:
        last_message = db_session.query(UserMessage).filter(or_(UserMessage.receiver==chatter, UserMessage.sender==chatter)).order_by(UserMessage.date_send).first()
        last_messages[last_message.sender] = last_message.message
    return render_template('map_neigh/messages_menu.html', chats=chats, last_messages=last_messages, chatters=chatters_list)


@app.route('/send_message', methods=['POST', 'GET'], strict_slashes=False)
def send_message():

    if request.method == 'POST':
        sender = current_user.username
        receiver = request.form.get('receiver')
        text = request.form.get('message')

        newMessage = UserMessage(sender=sender, receiver=receiver, message=text)
        db_session.add(newMessage)
        db_session.commit()

        flash('Wiadomość wysłana!')
        return redirect(url_for('messages_menu'))

    return render_template('map_neigh/send_message.html')


@app.route('/messages_menu/<username>', strict_slashes=False)
def get_messages(username):

    if current_user is None:
        flash('Najpierw musisz się zalogować')
        return redirect(url_for('.login'))

    messages = db_session.query(UserMessage).filter(or_(and_(UserMessage.sender == current_user.username, UserMessage.receiver == username), and_(UserMessage.sender == username, UserMessage.receiver == current_user.username))).all()
    return render_template('map_neigh/chat.html', messages=messages, username=username)