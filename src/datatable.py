from collections import namedtuple
from src import mongo
from querystring_parser import parser
import json

max_string_length = 50


class DataTablesServer:

    def __init__(self, request, columns, index, collection, group_by=None):
        self.columns = columns
        self.index = index
        self.collection = collection
        self.group_by = group_by

        # values specified by the datatable for filtering, sorting, paging
        self.request = parser.parse(request.query_string)
        self.dbh = mongo.db
        self.result_data = None  # results from the db
        self.records_filtered = 0  # total in the table after filtering
        self.records_total = 0  # total in the table unfiltered

        self.run_queries()

    def add_link_to_table(self, col, val, fields):
        uwu = ""
        if col == "fullgnomen":
            uwu = '<a href="/variant/{0}">{0}</a>'.format(val)
        elif col == "dn_no":
            uwu = '<a href="/patient/{0}">{0}</a>'.format(val)
        elif col == "gene":
            uwu = '<a href="/gene/{0}">{0}</a>'.format(val)
        elif fields == "given":
            uwu = val
        return uwu

    def output_result_on_fields(self, field):
        data_rows = []
        i = self.paging().start
        for row in self.result_data:
            data_row = []
            i += 1

            if field == "given":  # datatable for 'List All' page, shows all patients/variants/genes data with given columns
                data_row.append("<a href='/vus/{0}'>{1}</a>".format(row['_id'], i))
                for col in self.columns:
                    # get data from each mongo entry. for example: 'start': '241905405'
                    # col = start
                    # row = complete full entry (dict) with data for 1 patient (dicts, lists and strings)
                    # val = row[col] = mongoEntry['start'] = '241905405'
                    if col in row:
                        val = row[col]
                    # entries in Mongo are either another dict or a list (multiple keys) or string if only one key
                        if isinstance(val, dict):
                            # example: 'databaseReferences': {'dbSNP': 'rs547225878', 'omimRefs': '', 'omimMorbidRefs': ''}
                            val = json.dumps(val)  # convert dict to string
                        elif isinstance(val, list):
                            # example: 'familyMembers': [{'patientId': 12345, 'affected': False, 'relationType': 'MOTHER'},
                            # {'patientId': 67890, 'affected': False, 'relationType': 'FATHER'}]
                            val = ", ".join(val)  # convert list to string
                    else:
                        val = "-"
                    # after everything is converted to string, check if the string is too long to fit
                    # also check string entries that were already a string): example: 'start': '241905405', 'stop': '241905405'
                    if isinstance(val, str):
                        val = (val[:max_string_length] + '...') if len(val) > max_string_length else val

                    # make direct links if variant, gene or patient
                    uwu = self.add_link_to_table(col, val, fields="given")
                    # add data to the datatable
                    data_row.append(uwu)
                data_rows.append(data_row)

            # datatable for patients/genes/variants page. shows all available patients, genes or variants fields '#, id, total'
            # all a queried from mongodb. the contents of the "id" column changes to either patients, genes or variants
            if field == "queried":
                data_row.append(i)
                for col, val in row.items():
                    # get data from each row item. columns = ['#', '_id', 'total']; are mongo collection columns
                    # col = _id
                    # row = {'_id': 'NC_000014.8:g.105412831G>A', 'total': 1, 'protein': []}
                    # val = NC_000014.8:g.105412831G>A
                    uwu = ""
                    # Lookups specifying { _id: <someval> } refer to the _id index as their guide
                    if col == "_id":
                        # _id is either a variant, gene or patient. add direct links in datatable
                        uwu = self.add_link_to_table(col=self.group_by, val=val, fields="queried")
                    else:
                        # if column is anything else than _id, just add it without link
                        uwu = val
                    # add data to the datatable
                    data_row.append(uwu)
                data_rows.append(data_row)

        output = {}
        output['draw'] = str(int(self.request['draw']))
        output['recordsTotal'] = str(self.records_total)
        output['recordsFiltered'] = str(self.records_filtered)
        output['data'] = data_rows
        return output

    def run_queries(self):
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

        if self.group_by == "fullgnomen":
            group["$group"]["protein"] = {"$addToSet": "$pnomen"}
        pipeline = []

        if group:
            pipeline.append(group)
        if filter:
            pipeline.append(match)
        pipeline = pipeline + [{"$sort": sorting}, {"$skip": pages.start}]
        if pages.length >= 0:
            pipeline.append({"$limit": pages.length})
        self.result_data = list(self.dbh[self.collection].aggregate(pipeline))

        if group:
            # total amount unfiltered & total amount filtered (search bar)
            self.records_total = len(list(self.dbh[self.collection].aggregate([group])))
            self.records_filtered = len(list(self.dbh[self.collection].aggregate([group, match])))
        else:
            self.records_total = len(list(self.dbh[self.collection].find()))
            self.records_filtered = len(list(self.dbh[self.collection].find(filter)))

    def filtering(self):
        filter = {}
        if self.request['search']['value'] != "":
            # need to match for every field
            # the term put into search is logically concatenated with 'or' between all columns
            or_filter_on_all_columns = []
            for k, v in self.request["columns"].items():
                column_filter = {}
                try:
                    column_filter[self.columns[k]] = {'$regex': self.request['search']['value'], '$options': 'i'}
                    or_filter_on_all_columns.append(column_filter)
                except:
                    print(str(k), " is out of range prob")
            filter['$or'] = or_filter_on_all_columns
        return filter

    def sorting(self):
        order = {}
        # translation for sorting between datatables api and mongodb
        order_dict = {'asc': 1, 'desc': -1}

        for key, val in self.request['order'].items():
            order[self.columns[int(val['column'])]] = order_dict[val['dir']]
        return order

    def paging(self):
        pages = namedtuple('pages', ['start', 'length'])
        if (self.request['start'] != ""):
            pages.start = int(self.request['start'])
            pages.length = int(self.request['length'])
        return pages
