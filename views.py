from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin.contrib.mongoengine import ModelView
from datatable import DataTablesServer
from datatable_ajax import DataTablesServerAjax
import json

from models import Variant, User
from forms import RegisterForm, LoginForm

columns = ['#', '_id', 'total']

default_fields = ["dn_no", "gene_(gene)", "hgvs_genomic-level_nomenclature_(fullgnomen)",
                  "protein_(pnomen)", "omim(r)_refs", "omim(r)_morbid_refs"]
default_order = {"dn_no": 1, "gene_(gene)": 1, "hgvs_genomic-level_nomenclature_(fullgnomen)": 1}


def redirect_url():
    return request.args.get('next') or request.referrer or url_for('index')


def index():
    total_count = Variant.objects().all().count()
    variant_count = len(
        list(Variant.objects().aggregate({'$group': {'_id': '$hgvs_genomic-level_nomenclature_(fullgnomen)'}})))
    patient_count = len(list(Variant.objects().aggregate({'$group': {'_id': '$dn_no'}})))
    gene_count = len(list(Variant.objects().aggregate({'$group': {'_id': '$gene_(gene)'}})))
    return render_template("index.html", v=variant_count, p=patient_count, g=gene_count, t=total_count)


def variants():
    fields = columns
    if "protein" not in fields:
        fields.append("protein")
    return render_template('variants.html', fields=fields)


def variant(id):
    group_by = "hgvs_genomic-level_nomenclature_(fullgnomen)"
    # remove group_by from the fields list as its displayed at top of page and redundant for every row
    fields = list(filter(lambda x: x != group_by, default_fields))
    variants = Variant.objects.aggregate({"$match": {group_by: id}}, {"$sort": default_order})
    return render_template('variant.html', fields=fields, variants=variants, id=id)


def patients():
    return render_template("patients.html", patients=patients)


def patient(id):
    group_by = "dn_no"
    fields = list(filter(lambda x: x != group_by, default_fields))
    # order =
    variants = Variant.objects.aggregate({"$match": {group_by: id}}, {"$sort": default_order})

    return render_template('patient.html', variants=variants, fields=fields, id=id)


def genes():
    return render_template('genes.html')


def gene(id):
    group_by = "gene_(gene)"
    fields = list(filter(lambda x: x != group_by, default_fields))
    variants = Variant.objects.aggregate({"$match": {group_by: id}}, {"$sort": default_order})
    return render_template('gene.html', variants=variants, fields=fields, id=id)


def all():
    fields = default_fields
    for field in request.args:  # add fields that are being filtered on with get query to the table as column
        if field not in fields:
            fields.append(field)
    variants = Variant.objects.aggregate({"$match": request.args}, {"$sort": default_order}, {"$limit": 200})
    # print(variants[0])
    return render_template('all.html', variants=variants, fields=fields)


def vus(id):
    try:
        ret = Variant.objects(id=id)[0]
    except:
        print("problem " + id)
    return render_template('vus.html', variant=ret)


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


# create an app.route for your javascript. see above ^ for javascript implementation
def get_variant_data():
    return get_data("hgvs_genomic-level_nomenclature_(fullgnomen)")


def get_gene_data():
    return get_data("gene_(gene)")


def get_patient_data():
    return get_data("dn_no")


def get_all_data():
    index_column = "_id"
    collection = "variant"
    results = DataTablesServer(request, default_fields, index_column, collection).output_result()
    return json.dumps(results, sort_keys=True, default=str)


def get_data(group_by):
    index_column = "_id"
    collection = "variant"
    results = DataTablesServer(request, columns, index_column, collection, group_by).output_result()
    return json.dumps(results, sort_keys=True, default=str)
