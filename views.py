from flask import render_template, request, redirect, url_for, flash  # For flask implementation
from flask_excel import make_response_from_array
from bson import ObjectId  # For ObjectId to work
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mongoengine.wtf import model_form
from flask_admin.contrib.mongoengine import ModelView
from flask import Blueprint, jsonify, request
from datatable import DataTablesServer
import json

from models import Variant, User
from forms import RegisterForm, LoginForm


def redirect_url():
    return request.args.get('next') or request.referrer or url_for('index')


def index():
    variant_count = Variant.objects().all().count()
    patient_count = len(list(Variant.objects().aggregate({'$group': {'_id': '$patient_accession_no'}})))
    gene_count = len(list(Variant.objects().aggregate({'$group': {'_id': '$gene_(gene)'}})))
    return render_template("index.html", v=variant_count, p=patient_count, g=gene_count)


def variants():
    fields = columns
    return render_template('variants.html', fields=fields)


def variant(id):
    try:
        # ret = Variant.objects(id=id)[0]
        return render_template('variant.html', variant=ret)
    except:
        print("problem " + id)
        return render_template('404.html')


def patients():
    return render_template("patients.html", patients=patients)


def patient(id):
    fields = ["gene_(gene)", "cdna_(cnomen)", "protein_(pnomen)", "transcript", "analysis"]
    variants = []
    try:
        variants = Variant.objects(patient_accession_no=id)
    except:
        print("problem " + id)
    return render_template('patient.html', variants=variants, fields=fields, id=id)


def genes():
    return render_template('genes.html')


def gene(id):
    # as gene_(gene) cannot be an object name, need to use aggregation
    fields = ["gene_(gene)", "cdna_(cnomen)", "protein_(pnomen)", "transcript", "patient_accession_no"]
    variants = Variant.objects(__raw__={"gene_(gene)": id})

    return render_template('gene.html', variants=variants, fields=fields, id=id)


def export():
    # return make_response_from_array([[1,2], [3, 4]], "csv",
    #                                      file_name="export_data")
    pass


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


def login():
    if current_user.is_authenticated == True:
        return redirect(url_for('account'))
    form = LoginForm()
    if request.method == 'POST' and form.validate():
        check_user = User.objects(email=form.email.data).first()
        if check_user:
            if check_password_hash(check_user['password'], form.password.data):
                login_user(check_user)
                return redirect(url_for('account'))
            else:
                flash("Invalid username or password")
    return render_template('login.html', form=form)


@login_required
def account():
    return render_template('account.html', name=current_user.email)


@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Admin Stuff
class UserView(ModelView):
    column_filters = ['name']

    column_searchable_list = ('name', 'password')

    form_ajax_refs = {
        'tags': {
            'fields': ['name']
        }
    }


class VariantView(ModelView):
    column_filters = ['name']

    form_ajax_refs = {
        'tags': {
            'fields': ['name']
        }
    }


columns = ['#', '_id', 'total']


# create an app.route for your javascript. see above ^ for javascript implementation
def get_variant_data():
    return get_data("hgvs_genomic-level_nomenclature_(fullgnomen)")


def get_gene_data():
    return get_data("gene_(gene)")


def get_patient_data():
    return get_data("patient_accession_no")


def get_data(group_by):
    index_column = "_id"
    collection = "variant"
    results = DataTablesServer(request, columns, index_column, collection, group_by).output_result()
    return json.dumps(results)
