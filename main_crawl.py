import json
import time
import logging
import crawl_cmt, query
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
import asyncio


def main():
    ###___________crawl out post____
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    list_config = col_config.find({})
    # with open('config_test.json', 'r', encoding='utf-8') as readconfig:
    #     list_config = json.load(readconfig)
    for config in list_config:
        # a = crawl_cmt.crawl_out_post(config['website'], "https://linkhay.com/link/stream/new", config['crawl_page'])
        # print(a)
        list_link_cate = crawl_cmt.crawl_link_cate(config['crawl_link_cate'])
        for link_cate in list_link_cate:
            crawl_cmt.crawl_out_post(config['website'], link_cate, config['crawl_page'])

    # ####___________crawl in post____
    # col_config, col_temp_db, col_toppaper = query.connect_DB()
    # list_data = col_temp_db.find({}).limit(5)
    # for doc in list_data:
    #     comment = crawl_cmt.crawl_in_post(doc)
    #     print(comment, doc)
