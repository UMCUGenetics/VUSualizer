#!/usr/bin/env python3

"""
Usage: Import Alissa export in the form of .xsls into a MongoBD database.
       Make sure the data is in a sub folder called 'input'.
Python version: 3.7.1

Input .xlsx format
[Variant List] - spans 1A - 1E
[General Metadata] -
    - header spans 2A - 8B
    - value spans 2C - 8E
[Annotation Sources]
    - header spans 9A - 9B
    - subheader spans 9C - 22C
    - value spans 9D - 22H
[Empty line]
[Data Table of unknown length with first row as header]
"""

import os
from openpyxl import load_workbook
import time
import pymongo


def main():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client.vus.variant
    db.drop()

    start_time = time.time()

    for file in os.listdir("input"):
        # To prevent opening a cached version of the file
        if file.lower().endswith(".xlsx") and not file.lower().startswith("~"):
            print("#####\t\tParsing {}\t\t#####".format(file))
            patient = {}
            patient["dn_no"] = os.path.splitext(file)[0]
            annotation = {}
            data_headers = []
            section = ""

            wb = load_workbook(filename="input/" + file)
            sheet = wb.active
            for row in sheet:

                # First assess the section we're parsing
                if section == "":
                    # print("### Starting with parsing the Metadata section")
                    section = "metadata"
                    continue  # skip first row
                elif row[0].value == "Annotation Sources":
                    # print("### Detected switch to Annotation Sources section")
                    section = "annotation"
                elif section == "annotation" and row[2].value is None:
                    # print("### Detected switch to Data Table section")
                    patient["annotation_sources"] = annotation  # add previous section to total patient info
                    section = "data_table"
                    continue  # skip empty row

                # Parse data based on current section
                if section == "metadata":
                    patient[row[0].value.replace(".", "").replace(" ", "_").lower()] = row[2].value
                    pass
                elif section == "annotation":
                    annotation[row[2].value] = row[3].value
                    pass
                elif section == "data_table":
                    if len(data_headers) == 0:  # get headers
                        data_headers = [col.value for col in row]
                    else:  # values
                        variant = {}
                        for i in range(len(data_headers)):  # iterate headers
                            key = data_headers[i].replace(" ", "_").replace(".", "\uff0e").lower()
                            if key.startswith("father") or key.startswith("mother"):
                                continue
                            val = row[i].value
                            if key == "labels":
                                labels = val.split(";")
                                val = {}
                                for label in labels:
                                    labelInfo = label.split(",")
                                    val[labelInfo[0].replace(" ", "_").replace(".", "\uff0e").lower()] = labelInfo[1]
                            if val is not None and val != "":
                                variant[key] = val

                        # add variant info along with metadata to collection
                        variant.update(patient)
                        db.insert_one(variant)

    print("## \t\tFinished in {0:.2f} minutes".format((time.time() - start_time) / 60))


main()
