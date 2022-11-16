import datetime, time
import logging
import asyncio
def main():
    time_start_crawl_link = datetime.datetime.now().time()
    time.sleep(5)
    logging.info(f"time start crawl link: {time_start_crawl_link}, time end crawl link: {datetime.datetime.now().time()}")