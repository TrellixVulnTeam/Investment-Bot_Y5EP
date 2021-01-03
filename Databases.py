import pymongo

class MongoConnection(object):
    client = None
    database = None
    collection = None

    def __init__(self, host, dbname, colname):
        self.client = pymongo.MongoClient(host)
        self.database = self.client[dbname]
        self.collection = self.database[colname]