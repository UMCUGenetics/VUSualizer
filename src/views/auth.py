from flask import render_template, request, redirect, url_for, flash
from src import app, mongo, login_manager
from flask_login import login_required, login_user, logout_user, current_user
from src.forms import LoginForm, RegisterForm
from src.models import User
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get(form.email.data.strip())  # strip to remove any excess spaces
        if user:
            print(user)
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect(url_for('account'))
            flash('Wrong password')
        flash('There is no user with that email')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.get(form.email.data.strip())  # strip to remove any excess spaces
        if not user:
            hashed_password = generate_password_hash(form.password.data, method='sha256')
            new_user = User(email=form.email.data, password=hashed_password)
            new_user.save_to_db()
            login_user(new_user)
            return redirect(url_for('account'))
        flash("A user with this e-mail address already exists.")
    return render_template('register.html', form=form)


@app.route('/account')
@login_required
def account():
    return render_template('account.html', name=current_user.email)


"""
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate():
        print(request.form['email'])
        existing_user = User.get_by_email(request.form['email'])
        if existing_user:
            print("yatta desu ne")
            login_user(existing_user)
            return redirect(url_for('account'))
    return render_template('login.html', form=form)


@app.route('/register')
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate():
        existing_user = User.objects(email=form.email.data).first()
        if existing_user is None:
            hashpass = generate_password_hash(form.password.data, method='sha256')
            hey = User(form.name.data, form.email.data, hashpass).save()
            login_user(hey)
            return redirect(url_for('account'))
    
    return render_template('register.html', form=form)
"""
