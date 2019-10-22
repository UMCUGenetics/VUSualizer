from flask import Flask, render_template, request, redirect, url_for  # For flask implementation
from flask_excel import make_response_from_array

from bson import ObjectId  # For ObjectId to work
import os

from models import Variant

app = Flask(__name__)

def redirect_url():
    return request.args.get('next') or request.referrer or url_for('index')

@app.route("/")
def index():
    fields = ["patient_accession_no", "gene_(gene)", "chromosome",
            "exon", "transcript", "classification"]
    find = {}

    variants = Variant.objects.values().raw(find)

    return render_template('index.html', variants=variants, fields=fields)


@app.route("/export", methods=['GET'])
def export_records():
    return make_response_from_array([[1,2], [3, 4]], "csv",
                                          file_name="export_data")

if __name__ == "__main__":
    app.run(debug=True)