from flask import render_template, request, redirect, url_for
from src import app, mongo
from src.datatable import DataTablesServer
from flask_login import login_required, current_user
from bson import ObjectId
from collections import OrderedDict
from functools import wraps
import json


# make connection with MongoDB data
variant_col = mongo.db.variant
user_col = mongo.db.user

# _id is the primary key on elements in a mongodb collection; _id is automatically indexed. 
# Lookups specifying { _id: <someval> } refer to the _id index as their guide
mongo_columns = ['#', '_id', 'total']
default_fields = ["Details", "dn_no", "gene", "Position", "inheritanceMode", "cdna", "protein", "effect", "ref",
                  "genotype Patient", "genotype Mother", "genotype Father", "inheritedFrom", "GnomAD", "fullgnomen",
                  "transcript"]
default_order = {"dn_no": 1, "gene": 1}
variants = []


def login_required(f):
    '''Wrapper around the login_required() function of Flask, to also check the active status of the user'''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated is False or check_if_user_active(current_user):
            return redirect(url_for('account'))
        return f(*args, **kwargs)
    return decorated_function


def diaggen_role_required(f):
    '''Wrapper around the login_required() function of Flask, to also check the current role of the user'''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['ROLE_DIAGGEN', 'ROLE_ADMIN']:
            return redirect(url_for('account'))
        return f(*args, **kwargs)
    return decorated_function


def redirect_url():
    '''For redirecting the user to another page'''
    return request.args.get('next') or request.referrer or url_for('index')


all_fields = ["dn_no", "gene", "fullgnomen", "chromosome", "start", "stop", "exon", "protein", "classification",
              "zygosity", "inheritanceMode", "inheritedFrom", "variantAssessment", "transcript"]


# START HELPER FUNCTIONS

def group_and_count_on_field(field):
    '''Used for generating the totals on the Home page (app-route index)'''
    agg = variant_col.aggregate([
        {'$group': {'_id': field}},
        {'$count': "tot"}
    ])
    return list(agg)[0]['tot']


def render_individual_page(group_by, id, template):
    '''render individual page, for example patients-->patient or variants-->variant'''
    variants = variant_col.find({group_by: id})
    # remove group_by from the fields list as its displayed at top of page and redundant for every row
    fields = list(filter(lambda x: x != group_by, default_fields))
    return render_template(template, variants=variants, fields=fields, id=id)


def check_if_user_active(usercheck):
    if usercheck.active is True:
        return False
    else:
        return True


# END HELPER FUNCTIONS

# app.route functions
@app.route('/')
def index():
    total_count = variant_col.find().count()
    variant_count = group_and_count_on_field("$fullgnomen")
    patient_count = group_and_count_on_field("$dn_no")
    gene_count = group_and_count_on_field("$gene")
    return render_template("index.html", v=variant_count, p=patient_count, g=gene_count, t=total_count)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/patient/<id>')
@login_required
def patient(id):
    return render_individual_page("dn_no", id, "patient.html")


@app.route('/gene/<id>')
@login_required
@diaggen_role_required
def gene(id):
    return render_individual_page("gene", id, "gene.html")


@app.route('/variant/<id>')
@login_required
@diaggen_role_required
def variant(id):
    return render_individual_page("fullgnomen", id, "variant.html")


@app.route('/genes')
@login_required
@diaggen_role_required
def genes():
    return render_template("genes.html")


@app.route('/patients')
@login_required
def patients():
    return render_template("patients.html")


@app.route('/variants')
@login_required
@diaggen_role_required
def variants():
    fields = mongo_columns
    return render_template('variants.html', fields=fields)


@app.route('/all')
@login_required
@diaggen_role_required
def all():
    fields = all_fields
    return render_template('all.html', fields=fields)


@app.route('/vus/<id>')
@login_required
def vus(id):
    try:
        ret = variant_col.find_one({"_id": ObjectId(id)})
        # enable orderedDict to manipulate order of this dictionary before passing it to the VUS template
        ordered_ret = OrderedDict(ret)
        ordered_ret.move_to_end('chromosome', last=False) # sets chromosome at the top of VUS page
    except:
        print("problem " + id)
    return render_template('vus.html', variant=ordered_ret)


@app.route('/_get_variant_data')
@login_required
@diaggen_role_required
def get_variant_data():
    return get_data("fullgnomen")


@app.route('/_get_gene_data')
@login_required
@diaggen_role_required
def get_gene_data():
    return get_data("gene")


@app.route('/_get_patient_data')
@login_required
def get_patient_data():
    return get_data("dn_no")


@app.route('/_get_all_data')
@login_required
@diaggen_role_required
def get_all_data():
    index_column = "_id"
    collection = "variant"
    fields = all_fields
    results = DataTablesServer(request, fields, index_column, collection).output_result_on_fields(field="given")
    return json.dumps(results, sort_keys=True, default=str)

def get_data(group_by):
    index_column = "_id"
    collection = "variant"
    results = DataTablesServer(request, mongo_columns, index_column, collection, group_by).output_result_on_fields(field="queried")
    return json.dumps(results, sort_keys=True, default=str)
