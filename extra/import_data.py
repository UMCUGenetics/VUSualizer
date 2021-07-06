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
import io
import time
import pymongo
import warnings
import progressbar
import argparse
import sys
import logging
import logging.config
import yaml
from openpyxl import load_workbook

# configuration for the logging file. This file logs the import of excel files into MongoDB and errors
with open(os.path.dirname(__file__) + "/logging_config.yml", 'r') as configfile:
    logging.config.dictConfig(yaml.safe_load(configfile))

logger = logging.getLogger(__name__)
logger.debug("File upload script 'import_data.py' started")


def argparser():
    # function to enable commandline help functions. Makes use of the argparse installation.
    # also makes sure that required parameters are used, with basic file extension checks

    # Override of the error function in ArgumentParser from argparse
    # To display the original error message + help page in the terminal, when the wrong or no arguments are given
    class DefaultHelpParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('\nerror: %s\n' % message)
            self.print_help()
            logger.debug('error: %s' % message)
            sys.exit(1)  # exit program

    # Override of adding an extra action class in Action from argparse
    # To add an extra action that can check for file extensions and display the help page if wrong file extension
    def CheckExt(choices):
        class Act(argparse.Action):
            def __call__(self, parser, namespace, fname, option_string=None):
                for f in fname:
                    ext = os.path.splitext(f)[1][1:]
                    if ext not in choices:
                        option_string = '({})'.format(
                            option_string) if option_string else ''
                        parser.error("file doesn't end with {}{}".format(
                            choices, option_string))  # display error message
                    else:
                        setattr(namespace, self.dest, fname)
        return Act

    # required arguments and optional arguments for the terminal. A help page is automatically generated.
    parser = DefaultHelpParser(
        description=(
            "VUSualizer import data:\n"
            "Imports data from 'O:\AMG_bijlagen_WES_uitslagen' after transferring this data into\n"
            "the Dwergeik UMCU server. An additional script will notice new files in this folder\n"
            "and use these as a parameter for this script. This will update the local MongoDB."
        ),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "-v",
        "--version",
        action='version',
        version='%(prog)s 1.0')
    # puts following arguments under 'required', rather than the default 'optional'
    required_argument = parser.add_argument_group('required arguments')
    # add other file-extensions if needed: for example: CheckExt({'xlsx', 'xls})
    required_argument.add_argument(
        "-f",
        "--file",
        metavar='',
        required=True,
        nargs='+',
        action=CheckExt({'xlsx'}),
        help=".xlsx input, usage: -f /path/to/files/XXX.xlsx (or if multiple files, seperate with space: -f /path/to/files/XXX.xlsx /path/to/files/XXX2.xlsx'")

    args = parser.parse_args()
    return args.file


def main():
    '''Main function, for extracting the data from the excelformat and parse to the MongoDB'''
    # connection with MongoDB and the correct collection "vus"
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client.vus.variant
    files = argparser()  # get the files from the -f parameter

    # quiet the warning when loading the first xlsx
    warnings.simplefilter("ignore")
    start_time = time.time()

    # TODO: remove the progressbar dependency. Not needed for functionality and logging takes care of keeping track of files
    with progressbar.ProgressBar(max_value=len(files)) as bar:
        i = 0
        for file in bar(files):
            logger.debug('start uploading: %s' % file)
            i += 1
            # To prevent opening a cached version of the file
            if file.lower().endswith(".xlsx") and not file.lower().startswith("~"):
                patient = {}
                patient["dn_no"] = os.path.splitext(os.path.basename(file))[0]
                # If DNxxx.xlsx file is already in MongoDB, then first remove the old one.
                if db.count({"dn_no": patient["dn_no"]}) > 0:
                    logger.debug(
                        'dn_no: %s already present, start reuploading' % patient["dn_no"])
                    db.delete_many({"dn_no": patient["dn_no"]})
                    logger.debug('removed: %s from database' %
                                 patient["dn_no"])
                annotation = {}
                data_headers = []
                section = ""
                with open(file, "rb") as f:
                    in_mem_file = io.BytesIO(f.read())
                wb = load_workbook(in_mem_file)

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
                        # add previous section to total patient info
                        patient["annotation_sources"] = annotation
                        section = "data_table"
                        continue  # skip empty row

                    # Parse data based on current section
                    if section == "metadata":
                        patient[row[0].value.replace(".", "").replace(
                            " ", "_").lower()] = row[2].value
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
                                key = data_headers[i].replace(
                                    " ", "_").replace(".", "\uff0e").lower()

                                # skip everything that starts with father or mother etc since the key
                                # name contains patient number of parents
                                # TODO: implement this properly
                                if key.startswith("father") or key.startswith("mother") \
                                        or key.startswith("brother") or key.startswith("sister"):
                                    continue

                                # only use the name inbetween brackets to store, if last char is a right bracket
                                if key.endswith(")"):
                                    index_bracket_left = key.rfind("(")
                                    if index_bracket_left >= 0:
                                        key = key[index_bracket_left + 1:-1]

                                val = row[i].value
                                if key == "labels":
                                    labels = val.split(";")
                                    val = {}
                                    for label in labels:
                                        labelInfo = label.split(",")
                                        val[labelInfo[0].replace(" ", "_").replace(
                                            ".", "\uff0e").lower()] = labelInfo[1]
                                if val is not None and val != "":
                                    variant[key] = val

                            # add variant info along with metadata to collection
                            variant.update(patient)
                            db.insert_one(variant)
            bar.update(bar.value)
        logger.debug('finished uploading: %s' % file)
        # Moves file to other folder, to make uploading a new file (with same filename) possible on the UMCU server (for replacing)
        os.replace(file, os.path.dirname(__file__) +
                   "/verwerkt/" + os.path.basename(file))
    print("## \t\tFinished in {0:.2f} minutes".format(
        (time.time() - start_time) / 60))


main()
