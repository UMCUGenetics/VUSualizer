from collections import namedtuple
from pymongo import MongoClient
from flask import request

# from core.web.site import app
# from core.web.site.views_master import *


# translation for sorting between datatables api and mongodb
order_dict = {'asc': 1, 'desc': -1}


class DataTablesServer:

    def __init__(self, request, columns, index, collection, group_by=None):
        self.columns = columns
        self.index = index
        self.collection = collection
        self.group_by = group_by

        self.request_values = request.values  # values specified by the datatable for filtering, sorting, paging
        self.dbh = MongoClient()  # connection to your mongodb (see pymongo docs). this is defaulted to localhost
        self.result_data = None  # results from the db
        self.cardinality_filtered = 0  # total in the table after filtering
        self.cardinality = 0  # total in the table unfiltered

        self.run_queries()

    def output_result(self):
        output = {}
        output['sEcho'] = str(int(self.request_values['sEcho']))
        output['iTotalRecords'] = str(self.cardinality)
        output['iTotalDisplayRecords'] = str(self.cardinality_filtered)

        aaData_rows = []
        i = self.paging().start
        for row in self.result_data:
            aaData_row = []
            i += 1
            aaData_row.append(i)
            for col, val in row.items():
                if col in self.columns:
                    uwu = ""
                    if col == "_id":
                        if self.group_by == "hgvs_genomic-level_nomenclature_(fullgnomen)":
                            uwu = '<a href="/variant/{0}">{0}</a>'.format(val)
                        elif self.group_by == "patient_accession_no":
                            uwu = '<a href="/patient/{0}">{0}</a>'.format(val)
                        elif self.group_by == "gene_(gene)":
                            uwu = '<a href="/gene/{0}">{0}</a>'.format(val)
                    elif col == "protein":
                        temp = []
                        for x in val:
                            temp.append('<a href="/aaa?protein_(pnomen)={0}">{0}</a>'.format(x))
                        uwu = ", ".join(temp)
                    else:
                        # uwu = '<a href="/aaa?{1}={0}">{0}</a>'.format(val, col)
                        uwu = val
                    aaData_row.append(uwu)
            aaData_rows.append(aaData_row)

        output['aaData'] = aaData_rows
        return output

    def run_queries(self):
        mydb = self.dbh.vus
        pages = self.paging()  # pages has 'start' and 'length' attributes
        filter = self.filtering()  # the term entered into the datatable search
        sorting = self.sorting()  # the document field chosen to sort

        # get result from db
        match = {"$match": filter}
        group = {}
        if self.group_by is not None:
            group = {
                "$group": {
                    "_id": "$" + self.group_by,
                    "total": {
                        "$sum": 1
                    }
                }
            }

        if self.group_by == "hgvs_genomic-level_nomenclature_(fullgnomen)":
            group["$group"]["protein"] = {"$addToSet": "$protein_(pnomen)"}
        pipeline = []

        if group:
            pipeline.append(group)
        if filter:
            pipeline.append(match)
        pipeline = pipeline + [{"$sort": sorting}, {"$skip": pages.start}]
        if pages.length >= 0:
            pipeline.append({"$limit": pages.length})

        self.result_data = list(mydb[self.collection].aggregate(pipeline))

        if group:
            # total amount unfiltered
            self.cardinality = len(list(mydb[self.collection].aggregate([group])))
            # total amount filtered (search bar)
            self.cardinality_filtered = len(list(mydb[self.collection].aggregate([group, match])))
        else:
            self.cardinality = len(list(mydb[self.collection].find()))
            self.cardinality_filtered = len(list(mydb[self.collection].find(filter)))

    def filtering(self):
        # build your filter spec
        filter = {}
        if (self.request_values.has_key('sSearch')) and (self.request_values['sSearch'] != ""):
            # the term put into search is logically concatenated with 'or' between all columns
            or_filter_on_all_columns = []

            for i in range(len(self.columns)):
                column_filter = {}
                column_filter[self.columns[i]] = {'$regex': self.request_values['sSearch'], '$options': 'i'}
                or_filter_on_all_columns.append(column_filter)
                filter['$or'] = or_filter_on_all_columns
        return filter

    def sorting(self):
        order = {}
        # mongo translation for sorting order

        if (self.request_values['iSortCol_0'] != "") and (self.request_values['iSortingCols'] > str(0)):
            order = {}
            for i in range(int(self.request_values['iSortingCols'])):
                order[self.columns[int(self.request_values['iSortCol_' + str(i)])]] = order_dict[
                    self.request_values['sSortDir_' + str(i)]]
        return order

    def paging(self):
        pages = namedtuple('pages', ['start', 'length'])
        if (self.request_values['iDisplayStart'] != ""):  # and (int(self.request_values['iDisplayLength']) != -1):
            pages.start = int(self.request_values['iDisplayStart'])
            pages.length = int(self.request_values['iDisplayLength'])
        return pages
