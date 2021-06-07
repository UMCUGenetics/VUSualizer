from flask import render_template, request, redirect, url_for
from src import app, mongo
from flask_login import login_required, current_user
from bson import ObjectId
import json

from src.datatable import DataTablesServer

variant_col = mongo.db.variant
user_col = mongo.db.user

columns = ['#', '_id', 'total']

default_fields = ["dn_no", "gene", "fullgnomen",
                  "pnomen", "omim(r)_refs", "omim(r)_morbid_refs"]
default_order = {"dn_no": 1, "gene": 1, "fullgnomen": 1}

variants = []


def redirect_url():
    return request.args.get('next') or request.referrer or url_for('index')


def get_all_fields():
    uwu = variant_col.aggregate(
        [{"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}}, {"$unwind": "$arrayofkeyvalue"},
         {"$group": {"_id": None, "all_keys": {"$addToSet": "$arrayofkeyvalue.k"}}}])
    # print(list(uwu))
    return (list(uwu)[0]['all_keys'])


all_fields = ["dn_no", "gene", "fullgnomen", "chromosome", "cnomen", "pnomen", "exon", "classification",
              "codingeffect", "zygosity", "allelic_depth_allele_1", "allelic_depth_allele_2",
              "inheritance_mode", "inherited_from", "variant_assessment",
              "omimmorbidphenotype", "omimmorbidgenemim"]


#### START HELPER FUNCTIONS

def group_and_count_on_field(field):
    agg = variant_col.aggregate([
        {'$group': {'_id': field}},
        {'$count': "tot"}
    ])
    return list(agg)[0]['tot']
    # return 0


def render_individual_page(group_by, id, template):
    variants = variant_col.find({group_by: id})
    # remove group_by from the fields list as its displayed at top of page and redundant for every row
    fields = list(filter(lambda x: x != group_by, default_fields))
    return render_template(template, variants=variants, fields=fields, id=id)


def check_if_user_active(usercheck):
    if usercheck == True:
        return True
    else:
        return False


#### END HELPER FUNCTIONS

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
    if check_if_user_active(current_user.active):
        return render_individual_page("dn_no", id, "patient.html")
    else:
        return redirect(url_for('login'))


@app.route('/gene/<id>')
@login_required
def gene(id):
    if check_if_user_active(current_user.active):
        return render_individual_page("gene", id, "gene.html")
    else:
        return redirect(url_for('login'))


@app.route('/variant/<id>')
@login_required
def variant(id):
    if check_if_user_active(current_user.active):
        return render_individual_page("fullgnomen", id, "variant.html")
    else:
        return redirect(url_for('login'))


@app.route('/genes')
@login_required
def genes():
    if check_if_user_active(current_user.active):
        return render_template("genes.html")
    else:
        return redirect(url_for('login'))


@app.route('/patients')
@login_required
def patients():
    if check_if_user_active(current_user.active):
        return render_template("patients.html")
    else:
        return redirect(url_for('login'))


@app.route('/variants')
@login_required
def variants():
    if check_if_user_active(current_user.active):
        fields = columns
        if "protein" not in fields:
            fields.append("protein")
        return render_template('variants.html', fields=fields)
    else:
        return redirect(url_for('login'))


@app.route('/all')
@login_required
def all():
    if check_if_user_active(current_user.active):
        fields = all_fields
        return render_template('all.html', fields=fields)
    else:
        return redirect(url_for('login'))


@app.route('/vus/<id>')
@login_required
def vus(id):
    if check_if_user_active(current_user.active):
        try:
            ret = variant_col.find_one({"_id": ObjectId(id)})
        except:
            print("problem " + id)
        return render_template('vus.html', variant=ret)
    else:
        return redirect(url_for('login'))


@app.route('/_get_variant_data')
@login_required
def get_variant_data():
    if check_if_user_active(current_user.active):
        return get_data("fullgnomen")
    else:
        return redirect(url_for('login'))


@app.route('/_get_gene_data')
@login_required
def get_gene_data():
    if check_if_user_active(current_user.active):
        return get_data("gene")
    else:
        return redirect(url_for('login'))


@app.route('/_get_patient_data')
@login_required
def get_patient_data():
    if check_if_user_active(current_user.active):
        return get_data("dn_no")
    else:
        return redirect(url_for('login'))


@app.route('/_get_all_data')
@login_required
def get_all_data():
    if check_if_user_active(current_user.active):
        index_column = "_id"
        collection = "variant"
        fields = all_fields
        results = DataTablesServer(request, fields, index_column, collection).output_result_on_given_fields()
        return json.dumps(results, sort_keys=True, default=str)
    else:
        return redirect(url_for('login'))

def get_data(group_by):
    if check_if_user_active(current_user.active):
        index_column = "_id"
        collection = "variant"
        results = DataTablesServer(request, columns, index_column, collection,
                                group_by).output_result_on_queried_fields()
        return json.dumps(results, sort_keys=True, default=str)
    else:
        return redirect(url_for('login'))