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
        # print(json.dumps(self.request, sort_keys=True, indent=4))

        self.dbh = mongo.db
        self.result_data = None  # results from the db
        self.records_filtered = 0  # total in the table after filtering
        self.records_total = 0  # total in the table unfiltered

        self.run_queries()

    def add_data_to_page(self, col, val, fields):
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
            if field == "given":
                data_row.append("<a href='/vus/{0}'>{1}</a>".format(row['_id'], i))
                for col in self.columns:
                    if col in row:
                        val = row[col]
                        if isinstance(val, dict):
                            val = json.dumps(val)
                        elif isinstance(val, list):
                            val = ", ".join(val)
                    else:
                        val = "-"
                    if isinstance(val, str):
                        val = (val[:max_string_length] + '...') if len(val) > max_string_length else val
                    uwu = self.add_data_to_page(col, val, fields="given")
                    data_row.append(uwu)
                data_rows.append(data_row)
            if field == "queried":
                data_row.append(i)
                for col, val in row.items():
                    uwu = ""
                    if col == "_id":
                        uwu = self.add_data_to_page(col=self.group_by, val=val, fields="queried")
                    else:
                        uwu = val
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
