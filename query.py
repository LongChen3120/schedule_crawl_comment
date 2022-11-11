import pymongo
import json

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


def get_data(col, type_doc):
    # col_config, col_temp_db, col_toppaper = connect_DB()
    # list_doc_today = []

    # list_config = col_config.find({})
    # for config in list_config:
    #     for doc in col.find({"resourceUrl":{"$regex":config['website']},"type" : 6, "type_doc":type_doc}).limit(3):
    #         list_doc_today.append(doc)

    list_doc_today = []
    if type_doc == "get_all":
        for doc in col.find({}):
            list_doc_today.append(doc)
    else:
        for type in type_doc:
            for doc in col.find({"type" : 6, "type_doc":type}):
                list_doc_today.append(doc)
    return list_doc_today


def insert_col(col, list_data):
    col.insert_many(list_data)

def update_col(col, list_doc):
    for doc in list_doc:
        try:
            del doc['_id']
        except:
            pass
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


# def update_config():
#     col_config, col_temp_db, col_toppaper = connect_DB()
#     with open('config.json', 'r', encoding='utf-8') as read_config:
#         configs = json.load(read_config)
#     for config in configs:
#         try:
#             if col_config.find_one({"website":config['website']}):
#                 mapping_site = {"website":{"$regex":f"{config['website']}"}}
#                 update_vals = {"$set":config}
#                 update_web = col_config.update_one(mapping_site, update_vals)
#             else:
#                 col_config.insert_one(config)
#         except:
#             print(config)
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

# def check_update():
#     col_config, col_temp_db, col_toppaper, demo = connect_DB()
#     list_doc = demo.find({})
#     for doc in list_doc:
#         doc['comment'] = 10
#         update_col(demo, doc)
# check_update()