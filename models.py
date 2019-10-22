from pymodm import MongoModel, EmbeddedMongoModel, fields, connect
from pymodm.manager import QuerySet, Manager
from pymongo.write_concern import WriteConcern

connect("mongodb://localhost:27017/vus", alias="vus")

class Variant(MongoModel):
  chromosome = fields.CharField()

  class Meta:
    connection_alias = 'vus'
    write_concern = WriteConcern(j=True)
    final = True  # ignore if _cls field exists or not

