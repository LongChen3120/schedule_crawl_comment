import pymongo
import json
import datetime

# local mongodb://localhost:27017
# a huy mongodb://192.168.19.168:27017
def connect_DB():
    client = pymongo.MongoClient("mongodb://192.168.19.168:27017")
    db = client["PaPer"]
    col_temp_db = db["temp_collection"]
    col_toppaper = db["toppaper"]
    col_config = db["config_crawl_cmt"]

    return col_config, col_temp_db, col_toppaper


def find_config(mycol_config):
    my_config = mycol_config.find({})
    return my_config

def get_data(col, type_doc, time_create):
    list_doc_today = []
    for type in type_doc:
        for doc in col.find({"type" : 4, "type_doc":type, "comment": 1, "datetime": {
        "$lt": time_create
        }}):
            list_doc_today.append(doc)
    return list_doc_today


# col_config, col_temp_db, col_toppaper = connect_DB()
# time_now = datetime.datetime.now()
# print(get_data(col_temp_db, [1,2,3], time_now))


def insert_col(col, list_data):
    col.insert_many(list_data)


def insert_to_toppaper(col, list_data):
    list_new_doc = []
    for doc in list_data:
        if doc['comment'] > 0:
            list_new_doc.append(doc)
    if len(list_new_doc) > 0:
        col.insert_many(list_new_doc)


def update_col(col, list_doc):
    list_doc_new = []
    for doc in list_doc:
        doc_in_db = col.find_one({'url':doc['url']})
        if doc_in_db:
            doc_in_db['last_check'] = datetime.datetime.now()
            doc_in_db['comment'] = doc['comment']
            filter = {"url": doc['url']}
            vals = {"$set":doc_in_db}
            try:
                col.update_many(filter, vals)
            except:
                pass
        else:
            list_doc_new.append(doc)
            
    if len(list_doc_new) > 0:
        insert_col(col, list_doc_new)


def update_type_doc(col, list_doc):
    for doc in list_doc:
        filter = {"url": doc['url']}
        vals = {"$set":doc}
        try:
            col.update_many(filter, vals)
        except:
            pass


def delete_from_col(col, list_data):
    for doc in list_data:
        col.delete_one(doc)


# def insert_config():
#     col_config, col_temp_db, col_toppaper = connect_DB()
#     with open('config.json', 'r', encoding='utf-8') as read_config:
#         config = json.load(read_config)
#     col_config.insert_many(config)
# insert_config()


def update_config():
    col_config, col_temp_db, col_toppaper = connect_DB()
    with open('config_v2.json', 'r', encoding='utf-8') as read_config:
        configs = json.load(read_config)
    for config in configs:
        try:
            if col_config.find_one({"website":config['website']}):
                mapping_site = {"website":{"$regex":f"{config['website']}"}}
                update_vals = {"$set":config}
                update_web = col_config.update_one(mapping_site, update_vals)
            else:
                col_config.insert_one(config)
        except:
            print(config)
# update_config()

# def get_config():
#     col_config, col_temp_db, col_toppaper = connect_DB()
#     list_config = []
#     for config in col_config.find({}):
#         del config['_id']
#         list_config.append(config)
#     with open('config.json', 'w', encoding='utf-8') as write_config:
#         json.dump(list_config, write_config, ensure_ascii=False, indent=4)
# get_config()

# def check_update():
#     col_config, col_temp_db, col_toppaper, demo = connect_DB()
#     list_doc = demo.find({})
#     for doc in list_doc:
#         doc['comment'] = 10
#         update_col(demo, doc)
# check_update()
#hi
