from flask import Flask, render_template, request, redirect, url_for  # For flask implementation
from flask_excel import make_response_from_array

from bson import ObjectId  # For ObjectId to work
import os

from models import Variant

app = Flask(__name__)

def redirect_url():
    return request.args.get('next') or request.referrer or url_for('index')

@app.route("/")
@app.route("/home")
def index():
    find = {}
    fields = ["_id", "patient_accession_no", "gene_(gene)", "chromosome",
            "exon", "transcript", "classification"]

    for k, v in request.args.items():
      find[k] = v

    variants = Variant.objects.values().raw( request.args )

    return render_template('index.html', variants=variants, fields=fields)

@app.route("/variant")
def variant():
    variant_id = request.args.get("_id")
    try:
        ret = Variant.objects.values().raw({"_id": ObjectId(variant_id)}).first()
    except:
        print("problem " + variant_id)
    return render_template('variant.html', variant=ret)


@app.route("/export", methods=['GET'])
def export():
    #return make_response_from_array([[1,2], [3, 4]], "csv",
    #                                      file_name="export_data")
    pass


if __name__ == "__main__":
    app.run(debug=True)