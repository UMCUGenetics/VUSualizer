from flask import render_template, request, redirect, url_for
from src import app, mongo, login_manager
from flask_login import login_required, login_user, logout_user, current_user
from src.forms import LoginForm, RegisterForm
from src.models import User


# TODO fix login & register

@login_manager.user_loader
def load_user(user_email):
    User.get_by_email(user_email)


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
    """if request.method == 'POST' and form.validate():
        existing_user = User.objects(email=form.email.data).first()
        if existing_user is None:
            hashpass = generate_password_hash(form.password.data, method='sha256')
            hey = User(form.name.data, form.email.data, hashpass).save()
            login_user(hey)
            return redirect(url_for('account'))
    """
    return render_template('register.html', form=form)


@app.route('/account')
@login_required
def account():
    return render_template('account.html', name=current_user.email)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
