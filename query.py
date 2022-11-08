import pymongo
import json
import logging

# local mongodb://localhost:27017
# a huy mongodb://192.168.19.168:27017
def connect_DB():
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["PaPer"]
    col_temp_db = db["temp_collection"]
    col_toppaper = db["toppaper"]
    # col_1_day_before = db["1_day_before"]
    # col_2_day_before = db["2_day_before"]
    col_config = db["config_crawl_cmt"]

    return col_config, col_temp_db, col_toppaper


def find_config(mycol_config):
    my_config = mycol_config.find({}).limit(100)
    return my_config


def get_data(col, type_doc):
    col_config, col_temp_db, col_toppaper = connect_DB()
    list_doc_today = []

    list_config = col_config.find({})
    for config in list_config:
        for doc in col.find({"resourceUrl":{"$regex":config['website']},"type" : 6, "type_doc":type_doc}).limit(3):
            list_doc_today.append(doc)

    # list_doc_today = []
    # for doc in col.find({"type" : 6, "type_doc":type_doc}):
    #     list_doc_today.append(doc)
    return list_doc_today


async def insert_col_toppaper(col, list_data):
    for doc in list_data:
        del doc['type_doc']
        col.insert_one(doc)

def insert_col_temp_db(col, list_data):
    col.insert_many(list_data)

def update_col(col, doc):
    # del doc['_id']
    filter = {"url": doc['url']}
    vals = {"$set":doc}
    try:
        col.update_many(filter, vals)
    except Exception as e:
        print(e)
        # logging.info("exception when update docs,", e)


async def delete_from_col(col, list_data):
    for doc in list_data:
        col.delete_one(doc)


# def insert_config():
#     col_config, col_temp_db, col_toppaper = connect_DB()
#     with open('config.json', 'r', encoding='utf-8') as read_config:
#         config = json.load(read_config)
#     col_config.insert_many(config)
# insert_config()


# def update_config():
#     col_config, col_temp_db, col_toppaper
#     with open('./crawl_comment/config.json', 'r', encoding='utf-8') as read_config:
#         configs = json.load(read_config)
#     for config in configs:
#         try:
#             if mycol_config.find_one({"website":config['website']}):
#                 mapping_site = {"website":{"$regex":f"{config['website']}"}}
#                 update_vals = {"$set":config}
#                 update_web = mycol_config.update_one(mapping_site, update_vals)
#             else:
#                 mycol_config.insert_one(config)
#         except:
#             print(config)

# update_config()

