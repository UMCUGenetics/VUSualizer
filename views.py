from flask import render_template, request, redirect, url_for  # For flask implementation
from flask_excel import make_response_from_array
from bson import ObjectId  # For ObjectId to work
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


from models import Variant, User
from forms import RegisterForm, LoginForm

def redirect_url():
    return request.args.get('next') or request.referrer or url_for('index')

def index():
    find = ""
    fields = ["_id", "patient_accession_no", "gene_(gene)", "chromosome",
            "exon", "transcript", "classification"]
    print(request.query_string)
    for k, v in request.args.items():
      find += (k + "=\"" + v + "\"")

    #Variant(chromosome="uwu").save()  # Insert
    variants = Variant.objects()
    print(variants[0])

    return render_template('index.html', variants=variants, fields=fields)

def variants():
    find = ""
    fields = ["gene_(gene)", "cdna_(cnomen)", "protein_(pnomen)", "transcript", "patient_accession_no"]
    print(request.query_string)
    for k, v in request.args.items():
      find += (k + "=\"" + v + "\"")

    #Variant(chromosome="uwu").save()  # Insert
    variants = Variant.objects()
    print(variants[0])

    return render_template('variants.html', variants=variants, fields=fields)

def variant():
    variant_id = request.args.get("id")
    try:
        ret = Variant.objects(id=variant_id)[0]
    except:
        print("problem " + variant_id)
    return render_template('variant.html', variant=ret)

"""
@app.route("/patient")
def patient():
    fields = ["_id", "patient_accession_no", "gene_(gene)", "chromosome",
              "exon", "transcript", "classification"]
    patient_id = request.args.get("patient_accession_no")
    try:
        ret = Variant.objects.values().raw({"patient_accession_no": patient_id})
    except:
        print("problem " + patient_id)
    return render_template('patient.html', variants=ret, fields=fields, patient=patient_id)
"""

def export():
    #return make_response_from_array([[1,2], [3, 4]], "csv",
    #                                      file_name="export_data")
    pass

def register():
    form = RegisterForm()
    if request.method == 'POST':
        if form.validate():
            existing_user = User.objects(email=form.email.data).first()
            if existing_user is None:
                hashpass = generate_password_hash(form.password.data, method='sha256')
                hey = User(form.email.data, hashpass).save()
                login_user(hey)
                return redirect(url_for('account'))
    return render_template('register.html', form=form)

def login():
    if current_user.is_authenticated == True:
        return redirect(url_for('account'))
    form = LoginForm()
    if request.method == 'POST':
        if form.validate():
            check_user = User.objects(email=form.email.data).first()
            if check_user:
                if check_password_hash(check_user['password'], form.password.data):
                    login_user(check_user)
                    return redirect(url_for('account'))
    return render_template('login.html', form=form)

@login_required
def account():
    return render_template('account.html', name=current_user.email)

@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))