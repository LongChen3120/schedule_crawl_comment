from apscheduler.schedulers.blocking import BlockingScheduler
import time, datetime
import query, crawl_cmt, main_crawl
import queue
import threading
import logging
import asyncio
import os



#hu
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
            # logging.info(f"{threading.current_thread().name} update link: {doc['url']}")
            comment = crawl_cmt.crawl_in_post(doc, self.queue_post_err)
            if comment:
                doc['comment'] = comment
                doc['last_check'] = datetime.datetime.now()
                self.queue_update.put(doc)
            # logging.info(f"{threading.current_thread().name} finish update comment link: {doc['url']}")

        while self.queue_post_err.empty() == False:
            doc = self.queue_post_err.get()
            # logging.info(f"{threading.current_thread().name} reupdate link {doc['url']}")
            comment = crawl_cmt.crawl_in_post(doc, self.queue_post_save)
            if comment:
                doc['comment'] = comment
                doc['last_check'] = datetime.datetime.now()
                self.queue_update.put(doc)
                # logging.info(f"{threading.current_thread().name} finish reupdate comment link: {doc['url']}")




def detect_time():
    time_now = datetime.datetime.now()
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    main_crawl.main()
    if datetime.datetime.now().time().hour % 24 == 0:
        list_doc = query.get_data(col_temp_db, [1,2,3], time_now)
    elif datetime.datetime.now().time().hour % 6 == 0:
        list_doc = query.get_data(col_temp_db, [1, 2], time_now)
    else:
        list_doc = query.get_data(col_temp_db, [1], time_now)
    check_time(col_temp_db, col_toppaper, col_temp_db.find({}))
    create_thread(col_temp_db, list_doc)



def check_time(col_temp_db, col_toppaper, list_doc):
    list_doc_update = []
    list_doc_over_time = []
    list_del = []
    for doc in list_doc:
        if (datetime.datetime.now() - doc['datetime']).days == 1:
            doc['type_doc'] = 2
            list_doc_update.append(doc)
            # query.update_col(col_temp_db, doc)
        elif (datetime.datetime.now() - doc['datetime']).days == 2:
            doc['type_doc'] = 3
            list_doc_update.append(doc)
            # query.update_col(col_temp_db, doc)
        elif (datetime.datetime.now() - doc['datetime']).days > 2:
            if doc['comment'] == "0":
                list_del.append(doc)
            else:
                del doc['type_doc']
                del doc['_id']
                list_doc_over_time.append(doc)
    query.update_type_doc(col_temp_db, list_doc_update)
    if len(list_del) > 0:
        query.delete_from_col(col_temp_db, list_del)
    if len(list_doc_over_time) > 0:
        query.delete_from_col(col_temp_db, list_doc_over_time)
        query.insert_col(col_toppaper, list_doc_over_time)


def create_thread(col_temp_db, list_doc):
    list_thread = []
    queue_doc = queue.Queue()
    queue_update = queue.Queue()
    queue_post_err = queue.Queue()
    queue_post_save = queue.Queue()
    for doc in list_doc:
        queue_doc.put(doc)

    for i in range(3): #5
        thread = My_thread(queue_doc, queue_update, queue_post_err, queue_post_save)
        thread.daemon
        thread.start()
        list_thread.append(thread)

    for thread in list_thread:
        thread.join()

    list_doc_update = []
    while queue_update.empty() == False:
        doc = queue_update.get()
        list_doc_update.append(doc)
    query.update_col(col_temp_db, list_doc_update)

    with open('./log/post_error.txt', 'w', encoding='utf-8') as write_post_err:
        while queue_post_save.empty() == False:
            cate_save = queue_post_save.get()
            write_post_err.write(cate_save['url'] + "\n")



def main():
    with open('./log/log_main.log', 'w'):
        pass
    logging.basicConfig(filename='./log/log_main.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info("\n\n_____________________________new_log_____________________________")
    detect_time()


if __name__ == '__main__':
    start_time = time.time()
    with open('./log/log_main.log', 'w'):
        pass
    main()
    # scheduler = BlockingScheduler()
    # scheduler.add_job(main, 'interval', hours=1, max_instances=5)
    # print('Press Ctrl+C to exit !')
    # try:
    #     scheduler.start()
    # except (KeyboardInterrupt, SystemExit):
    #     pass

    print("done ! \ntime: ",(time.time() - start_time))



# thay vì check link ở db trước rồi mới quét link mới và comment mới về thì quét link và comment về trước. link mới lưu với time check, 
# link cũ đã có trong db thì cập nhật comment với time_check. xong việc mới kiểm tra trong db có link nào chưa được cập nhật thì mới quét detail.
