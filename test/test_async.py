from apscheduler.schedulers.blocking import BlockingScheduler
from concurrent.futures import ThreadPoolExecutor
import time, datetime
import query, main_crawl
import queue
import threading
import logging
import asyncio
import os
import psutil, pymongo


def connect_DB():
    client = pymongo.MongoClient("mongodb://192.168.19.168:27017")
    db = client["PaPer"]
    col_temp_db = db["temp_collection"]
    col_toppaper = db["toppaper"]
    col_config = db["config_crawl_cmt"]

    return col_config, col_temp_db, col_toppaper


def run(dfd):
    col_config, col_temp_db, col_toppaper = connect_DB()
    thread = threading.current_thread()
    logging.info(f"{thread.name} start")
    time_start_check_comment = datetime.datetime.now().time()
    data = col_temp_db.find({})
    time.sleep(5)
    logging.info(f"time start check comment: {time_start_check_comment}, time end check commetn: {datetime.datetime.now().time()}")




def detect_time(executor):
    executor.map(run, range(3))

def main():
    pid = os.getpid()
    global data
    with ThreadPoolExecutor(max_workers=3) as executor:
        detect_time(executor)
    logging.info(f"___count of thread: {threading.active_count()}")
    python_process = psutil.Process(pid)
    
    memoryUse = python_process.memory_info()[0]  # memory use in GB...I think
    thread = threading.current_thread()
    print(f'Worker thread: name={thread.name}, idnet={threading.get_ident()}, id={threading.get_native_id()}')
    logging.info(f"memory use:{memoryUse}" )


if __name__ == '__main__':
    with open('./log/log_main_async.log', 'w'):
        pass
    logging.basicConfig(filename='./log/log_main_async.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info("\n\n_____________________________new_log_____________________________")

    # main()

    start_time = time.time()
    scheduler = BlockingScheduler()
    scheduler.add_job(main, 'interval', seconds=7)
    print('Press Ctrl+C to exit !')
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

    # print("done ! \ntime: ",(time.time() - start_time)) 38903808
