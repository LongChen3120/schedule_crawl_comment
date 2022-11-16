import json
import time
import logging
import crawl_cmt, query
import queue
import threading
import asyncio


class My_thread(threading.Thread):
    def __init__(self, queue_cate, config, queue_cate_err, queue_cate_save):
        threading.Thread.__init__(self)
        self.queue_cate = queue_cate
        self.config = config
        self.queue_cate_err = queue_cate_err
        self.queue_cate_save = queue_cate_save
    
    def run(self):
        main_handler(self.queue_cate, self.config, self.queue_cate_err, self.queue_cate_save)
 
def main_handler(queue_cate, config_site, queue_cate_err, queue_cate_save):
    while queue_cate.empty() == False:  
        link_cate = queue_cate.get()
        logging.info(f"crawl: {link_cate}")
        crawl_cmt.crawl_out_post(link_cate, config_site, queue_cate_err)

    while queue_cate_err.empty() == False:
        cate_err = queue_cate_err.get()
        crawl_cmt.crawl_out_post(cate_err, config_site, queue_cate_save)

    with open('./log/cate_error.txt', 'w', encoding='utf-8') as write_cate_err:
        while queue_cate_save.empty() == False:
            cate_save = queue_cate_save.get()
            write_cate_err.writelines(cate_save)



def main():
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    configs = col_config.find({})

    list_thread = []
    queue_cate = queue.Queue()
    queue_cate_err = queue.Queue()
    queue_cate_save = queue.Queue()

    for config in configs:
        del config['_id']
        list_link_cate = crawl_cmt.crawl_link_cate(config)
        queue_cate.put(config['website'])
        for link_cate in list_link_cate: 
            queue_cate.put(link_cate)

        for i in range(3): #5
            thread = My_thread(queue_cate, config, queue_cate_err, queue_cate_save)
            list_thread.append(thread)
            thread.daemon
            thread.start()

        for thread in list_thread:
            thread.join()