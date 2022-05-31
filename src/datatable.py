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

    def output_result_on_given_fields(self):
        output = {}
        output['draw'] = str(int(self.request['draw']))
        output['recordsTotal'] = str(self.records_total)
        output['recordsFiltered'] = str(self.records_filtered)

        data_rows = []
        i = self.paging().start

        for row in self.result_data:
            data_row = []
            i += 1
            data_row.append("<a href='/vus/{0}'>{1}</a>".format(row['_id'], i))
            for col in self.columns:
                if col in row:
                    val = row[col]
                else:
                    val = "-"

                if isinstance(val, dict):
                    print("YAS")
                    val = json.dumps(val)
                    print(val)
                elif isinstance(val, list):
                    val = ", ".join(val)

                if isinstance(val, str):
                    val = (val[:max_string_length] + '...') if len(val) > max_string_length else val

                uwu = ""
                if col == "fullgnomen":
                    uwu = '<a href="/variant/{0}">{0}</a>'.format(val)
                elif col == "dn_no":
                    uwu = '<a href="/patient/{0}">{0}</a>'.format(val)
                elif col == "gene":
                    uwu = '<a href="/gene/{0}">{0}</a>'.format(val)
                else:
                    uwu = val
                data_row.append(uwu)
            data_rows.append(data_row)
        output['data'] = data_rows
        return output

    def output_result_on_queried_fields(self):
        output = {}
        output['draw'] = str(int(self.request['draw']))
        output['recordsTotal'] = str(self.records_total)
        output['recordsFiltered'] = str(self.records_filtered)

        data_rows = []
        i = self.paging().start
        for row in self.result_data:
            data_row = []
            i += 1
            data_row.append(i)
            for col, val in row.items():
                uwu = ""
                if col == "_id":
                    if self.group_by == "fullgnomen":
                        uwu = '<a href="/variant/{0}">{0}</a>'.format(val)
                    elif self.group_by == "dn_no":
                        uwu = '<a href="/patient/{0}">{0}</a>'.format(val)
                    elif self.group_by == "gene":
                        uwu = '<a href="/gene/{0}">{0}</a>'.format(val)
                elif col == "total":
                    uwu = val
                else:
                    # filtering like this doesn't work yet
                    # uwu = '<a href="/all?{1}={0}">{0}</a>'.format(val, col)
                    uwu = val
                data_row.append(uwu)
            data_rows.append(data_row)

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
        """
        build your filter spec
        "search": {
            "regex": "false",
            "value": ""
        },
        :return: filter dict
        """
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
        """
        mongo translation for sorting order
        "order": {
            "0": {
                "column": "0",
                "dir": "asc"
            }
        },
        :return: order dict { col name : direction }
        """
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
