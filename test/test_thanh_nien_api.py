import requests, re
from lxml import html
import pymongo
from apscheduler.schedulers.blocking import BlockingScheduler
import time, datetime
import queue
import threading
import logging
import asyncio
import os



api = "https://thanhnien.vn/api/comments/get/by-obj?object_type=20&object_id={param_0}"
header={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42'}


def crawl_in_post(doc, queue_post_err):
    link_post = doc['url']
    config_site = check_config(link_post)
    type_crawl = config_site['comment_in_post']['type_crawl']
    try:
        if type_crawl == 1:
            res = send_request(link_post, type_crawl, param_scroll_down=False)
            lxml = html.fromstring(res.text, 'lxml')
            comment = detect_type(1, lxml, config_site['comment_in_post'])[0]
            comment = re.findall(r'\d+', comment)[0]

        elif type_crawl == 2:
            website = send_request(link_post, type_crawl, param_scroll_down=False)
            comment = detect_type(2, website, config_site['comment_in_post'])
            comment = re.findall(r'\d+', comment[0].get_attribute('textContent'))[0]
            website.close()

        elif type_crawl == 3:
            list_api = detect_type_param(link_post, config_site['api'])
            for api in list_api:
                try:
                    res = send_request(api, 1, param_scroll_down= False)
                    data = detect_responseType(config_site['comment_in_post']['responseType'], res)
                    try:
                        comment = check_regex(config_site['comment_in_post']['detect']['re'], [str(data)])[0]
                        comment = re.findall(r'\d+', comment)[0]
                        logging.info(f"ok: {api}")
                        break
                    except: # xảy ra khi res.status_code() = 200 nhưng token hết hạn
                        comment = doc['comment']
                        logging.info(f"412, api: {api}")
                except: # xảy ra khi res.status_code() = 403
                    logging.info(f"res status:{res.status_code}, api: {api}")
                    comment = ""
                    pass

                
    except:
        queue_post_err.put(doc)
        comment = "0"

    return comment


def connect_DB():
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["PaPer"]
    col_temp_db = db["temp_collection"]
    col_toppaper = db["toppaper"]
    col_config = db["config_crawl_cmt"]

    return col_config, col_temp_db, col_toppaper


def check_config(url):
    col_config, col_temp_db, col_toppaper = connect_DB()
    list_web_config = col_config.find({})
    for config in list_web_config:
        domain = re.split('/|\\.', config['website'])[2]
        if domain in url:
            return config


def send_request(link_cate, type_crawl, param_scroll_down):
    if type_crawl == 1:
        time.sleep(5)
        res = requests.get(link_cate, headers=header, timeout=10)
        return res


def detect_type(type_crawl, lxml, config):
    if type_crawl == 1:
        if config['detect']['type'] == 1:
            list_result = lxml.xpath(config['detect']['xpath'])
        elif config['detect']['type'] == 2:
            pass
        elif config['detect']['type'] == 3:
            list_result = lxml.xpath(config['detect']['xpath'])
            list_result = check_regex(config['detect']['re'], list_result)

    return list_result


def detect_type_param(link_post, config):
    api = config['url']
    list_api = []
    for param in config['params']:
        if param['type'] == 1:
            id_post = get_id_post(link_post)
            api = api.replace('param_0', id_post)
            list_api.append(api)
        elif param['type'] == 2:
            list_api.pop(0)
            for val in param['values']:
                list_api.append(api.replace('param_1', val))
    return list_api


def get_id_post(link_post):
    id_post = re.findall(r'\d+', link_post)[-1]
    return id_post


def detect_responseType(response_type, res):
    if response_type == 1:
        return html.fromstring(res.text, 'lxml')
    elif response_type == 2:
        return res.json()


def check_regex(regex, list_link):
    list_result = []
    for link in list_link:
        result = re.findall(regex, link)
        if result:
            list_result.append(result[0])
    return list(set(list_result))


class My_thread(threading.Thread):
    def __init__(self, queue_doc, queue_update, queue_post_err, queue_post_save):
        threading.Thread.__init__(self)
        self.queue_doc = queue_doc
        self.queue_update = queue_update
        self.queue_post_err = queue_post_err
        self.queue_post_save = queue_post_save

    def run(self):
        while self.queue_doc.empty() == False:
            doc = self.queue_doc.get()
            logging.info(f"{threading.current_thread().name} update link: {doc['url']}")
            comment = crawl_in_post(doc, self.queue_post_err)
            if comment:
                doc['comment'] = comment
                doc['last_check'] = datetime.datetime.now()
                self.queue_update.put(doc)
            logging.info(f"{threading.current_thread().name} finish update comment link: {doc['url']}")

        while self.queue_post_err.empty() == False:
            doc = self.queue_post_err.get()
            # logging.info(f"{threading.current_thread().name} reupdate link {doc['url']}")
            comment = crawl_in_post(doc, self.queue_post_save)
            if comment:
                doc['comment'] = comment
                doc['last_check'] = datetime.datetime.now()
                self.queue_update.put(doc)
                # logging.info(f"{threading.current_thread().name} finish reupdate comment link: {doc['url']}")



def get_data(col, type_doc):
    # col_config, col_temp_db, col_toppaper = connect_DB()
    # list_doc_today = []

    # list_config = col_config.find({})
    # for config in list_config:
    #     for doc in col.find({"resourceUrl":{"$regex":config['website']},"type" : 6, "type_doc":type_doc}).limit(3):
    #         list_doc_today.append(doc)

    list_doc_today = []
    for type in type_doc:
        for doc in col.find({"resourceUrl":{"$regex":"https://thanhnien"},"type" : 6, "type_doc":type}):
            list_doc_today.append(doc)
    return list_doc_today



def detect_time():
    col_config, col_temp_db, col_toppaper = connect_DB()
    # if datetime.datetime.now().time().hour % 24 == 0:
    #     list_doc = query.get_data(col_temp_db, [1,2,3])
    #     check_time(col_temp_db, col_toppaper, list_doc)
    #     create_thread(col_temp_db, list_doc)
    #     asyncio.gather()
    #     main_crawl.main()

    # elif datetime.datetime.now().time().hour % 6 == 0:
    #     list_doc = query.get_data(col_temp_db, [1, 2])
    #     check_time(col_temp_db, col_toppaper, list_doc)
    #     create_thread(col_temp_db, list_doc)
    #     main_crawl.main()

    # elif datetime.datetime.now().time().hour % 2 == 0:
    #     list_doc = query.get_data(col_temp_db, [1])
    #     check_time(col_temp_db, col_toppaper, list_doc)
    #     create_thread(col_temp_db, list_doc)
    #     main_crawl.main()

    # else:
    list_doc = get_data(col_temp_db, [1,2,3])
    #     check_time(col_temp_db, col_toppaper, list_doc)
    create_thread(col_temp_db, list_doc)




def create_thread(col_temp_db, list_doc):
    list_thread = []
    queue_doc = queue.Queue()
    queue_update = queue.Queue()
    queue_post_err = queue.Queue()
    queue_post_save = queue.Queue()
    for doc in list_doc:
        queue_doc.put(doc)

    for i in range(1): #5
        thread = My_thread(queue_doc, queue_update, queue_post_err, queue_post_save)
        thread.daemon
        thread.start()
        list_thread.append(thread)

    for thread in list_thread:
        thread.join()




def main():
    with open('./log/log_main_async.log', 'w'):
        pass
    logging.basicConfig(filename='./log/log_main_async.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info("\n\n_____________________________new_log_____________________________")
    detect_time()


if __name__ == '__main__':
    start_time = time.time()
    main()
    # scheduler = BlockingScheduler()
    # scheduler.add_job(main, 'interval', hours=1)
    # print('Press Ctrl+C to exit !')
    # try:
    #     scheduler.start()
    # except (KeyboardInterrupt, SystemExit):
    #     pass

    print("done ! \ntime: ",(time.time() - start_time))