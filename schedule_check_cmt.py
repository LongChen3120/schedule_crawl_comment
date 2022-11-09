from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time, datetime
import query, crawl_cmt, main_crawl
import queue
import threading
import logging
import asyncio

 

class My_thread(threading.Thread):
    def __init__(self, queue_doc):
        threading.Thread.__init__(self)
        self.queue_doc = queue_doc
    
    def run(self):
        while self.queue_doc.empty() == False:
            doc = self.queue_doc.get()
            logging.info(f"{threading.current_thread().name} update link: {doc['url']}")
            comment = crawl_cmt.crawl_in_post(doc, queue_post_err)
            if comment:
                doc['comment'] = comment
                doc['last_check'] = datetime.datetime.now()
                queue_update.put(doc)
            logging.info(f"{threading.current_thread().name} finish update comment link: {doc['url']}")

        while queue_post_err.empty() == False:
            doc = queue_post_err.get()
            logging.info(f"{threading.current_thread().name} reupdate link {doc['url']}")
            comment = crawl_cmt.crawl_in_post(doc, queue_post_save)
            if comment:
                doc['comment'] = comment
                doc['last_check'] = datetime.datetime.now()
                queue_update.put(doc)
                logging.info(f"{threading.current_thread().name} finish reupdate comment link: {doc['url']}")




async def detect_time():
    # if datetime.datetime.now().time().hour % 24 == 0:
        await asyncio.gather(check_comment_today(), check_comment_1_day_before(), check_comment_2_day_before())
    #     print("done check")
    #     main_crawl.main()
    #     return 3
    # elif datetime.datetime.now().time().hour % 6 == 0:
    #     await asyncio.gather(check_comment_today(), check_comment_1_day_before())
    #     main_crawl.main()
    #     return 2
    # elif datetime.datetime.now().time().hour % 2 == 0:
    #     await check_comment_today()
    #     main_crawl.main()
    #     return 1
    # else:
    #     await check_comment_today()
    #     # main_crawl.main()
    #     return 0


async def check_comment_today():
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    list_doc = query.get_data(col_temp_db, type_doc=1)
    list_doc_over_time = await check_time(queue_doc_today, list_doc, time_out = 1)
    if len(list_doc_over_time) > 0:
        for doc in list_doc_over_time:
            doc['type_doc'] = 2
            query.update_col(col_temp_db, doc)
    create_thread(queue_doc_today)
    


async def check_comment_1_day_before():
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    list_doc = query.get_data(col_temp_db, type_doc=2)
    list_doc_over_time = await check_time(queue_doc_1day_before, list_doc, time_out = 2)
    if len(list_doc_over_time) > 0:
        for doc in list_doc_over_time:
            doc['type_doc'] = 3
            query.update_col(col_temp_db, doc)
    create_thread(queue_doc_1day_before)


async def check_comment_2_day_before():
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    list_doc = query.get_data(col_temp_db, type_doc=3)
    list_doc_over_time = await check_time(queue_doc_2day_before, list_doc, time_out = 3)
    if len(list_doc_over_time) > 0:
        await asyncio.gather(query.insert_col_toppaper(col_toppaper, list_doc_over_time), query.delete_from_col(col_temp_db, list_doc_over_time))
    create_thread(queue_doc_2day_before)


async def check_time(queue_doc, list_doc, time_out):
    list_doc_over_time = []
    for doc in list_doc:
        if (datetime.datetime.now() - doc['datetime']).days == time_out:
            list_doc_over_time.append(doc)
        else:
            queue_doc.put(doc)

    return list_doc_over_time
 

def create_thread(queue_doc):
    list_thread = []
        
    for i in range(3): #5
        thread = My_thread(queue_doc)
        thread.daemon
        thread.start()
        list_thread.append(thread)

    for thread in list_thread:
        thread.join()


async def main():
    with open('./log/log_main.log', 'w'):
        pass
    logging.basicConfig(filename='./log/log_main.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info("\n\n_____________________________new_log_____________________________")

    global queue_doc_today, queue_doc_1day_before, queue_doc_2day_before, queue_update, queue_post_err, queue_post_save
    queue_doc_today = queue.Queue()
    queue_doc_1day_before = queue.Queue()
    queue_doc_2day_before = queue.Queue()
    queue_update = queue.Queue()
    queue_post_err = queue.Queue()
    queue_post_save = queue.Queue()

    type_data = await detect_time()

    col_config, col_temp_db, col_toppaper = query.connect_DB()
    while queue_update.empty() == False:
        doc = queue_update.get()
        query.update_col(col_temp_db, doc)

    with open('./log/post_error.txt', 'w', encoding='utf-8') as write_post_err:
        while queue_post_save.empty() == False:
            cate_save = queue_post_save.get()
            write_post_err.write(cate_save['url'] + "\n")


if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(main())
    # scheduler = AsyncIOScheduler()
    # scheduler.add_job(main, 'interval', minutes=5)
    # scheduler.start()
    # try:
    #     asyncio.get_event_loop().run_forever()
    # except:
    #     pass

    print("done ! \ntime: ",(time.time() - start_time))
