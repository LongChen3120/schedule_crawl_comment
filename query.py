import pymongo
import json
import logging


def connect_DB():
    client = pymongo.MongoClient("mongodb://192.168.19.168:27017")
    db = client["PaPer"]
    col_today = db["toppaper"]
    col_1_day_before = db["1_day_before"]
    col_2_day_before = db["2_day_before"]
    col_config = db["config_crawl_cmt"]

    return col_config, col_today, col_1_day_before, col_2_day_before


def find_config(mycol_config):
    my_config = mycol_config.find({}).limit(100)
    return my_config


def get_data(col):
    # mycol_config, mycol_today, mycol_1_day_before, mycol_2_day_before = connect_DB()
    # list_doc_today = []

    # list_config = mycol_config.find({})
    # for config in list_config:
    #     for doc in col.find({"resourceUrl":{"$regex":config['website']}}).limit(10):
    #         list_doc_today.append(doc)

    list_doc_today = []
    for doc in col.find({"type" : 6}):
        list_doc_today.append(doc)
    return list_doc_today


async def insert_col(col, list_data):
    col.insert_many(list_data)

def insert_coll(col, list_data):
    col.insert_many(list_data)

def update_col(col, doc):
    filter = {"url": doc['url']}
    vals = {"$set":doc}
    try:
        col.update_one(filter, vals)
    except Exception as e:
        logging.info("exception when update docs,", e)


async def delete_from_col(col, list_data):
    for doc in list_data:
        col.delete_one(doc)


# def insert_config():
#     mycol_config, mycol_today, mycol_1_day_before, mycol_2_day_before = connect_DB()
#     with open('config.json', 'r', encoding='utf-8') as read_config:
#         config = json.load(read_config)
#     mycol_config.insert_many(config)
# insert_config()


# def update_config():
#     mycol_config, mycol_today, mycol_1_day_before, mycol_2_day_before = connect_DB()
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

