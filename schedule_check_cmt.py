from apscheduler.schedulers.blocking import BlockingScheduler
import time, datetime
import query, crawl_cmt, main_crawl
import queue
import threading
import logging
import asyncio
import os


def check_comment_detail(col_temp_db, list_doc):
    for doc in list_doc:
        comment = crawl_cmt.crawl_in_post(doc)
        if comment:
            doc['comment'] = comment
            doc['last_check'] = datetime.datetime.now()
            query.update_col(col_temp_db, [doc])


def detect_time():
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    time_create = datetime.datetime.now()
    main_crawl.main()
    if datetime.datetime.now().time().hour % 6 == 0:
        check_time(col_temp_db, col_toppaper, col_temp_db.find({"datetime": {"$lt": time_create}}))
        list_doc = query.get_data(col_temp_db, [1], time_create)
        print(len(list_doc))
        check_comment_detail(col_temp_db, list_doc)


def check_time(col_temp_db, col_toppaper, list_doc):
    list_doc_update = []
    list_doc_over_time = []
    list_del = []
    for doc in list_doc:
        if (datetime.datetime.now() - doc['datetime']).days == 1:
            doc['type_doc'] = 2
            list_doc_update.append(doc)
        elif (datetime.datetime.now() - doc['datetime']).days == 2:
            doc['type_doc'] = 3
            list_doc_update.append(doc)
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
    # main()
    scheduler = BlockingScheduler()
    scheduler.add_job(main, 'interval', minutes=30, max_instances=5)
    print('Press Ctrl+C to exit !')
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

    print("done ! \ntime: ",(time.time() - start_time))



# thay vì check link ở db trước rồi mới quét link mới và comment mới về thì quét link và comment về trước. link mới lưu với time check, 
# link cũ đã có trong db thì cập nhật comment với time_check. xong việc mới kiểm tra trong db có link nào chưa được cập nhật thì mới quét detail.
