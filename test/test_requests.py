import requests, datetime, logging, time

header={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42'}

api ="https://thanhnien.vn/api/comments/get/by-obj?object_type=20&object_id=1520782"

count_request = 0
message = ""
time_start = datetime.datetime.now().time()
time_sleep = 0.5
while True:
    time.sleep(time_sleep)
    res = requests.get(api, headers=header)
    
    if res.status_code == 200:
        count_request += 1
        if res.json()['error_code'] == -412:
            message = "err 412"
            break
    else:
        message = "err 403"
        break
time_end = datetime.datetime.now().time()

logging.basicConfig(filename='./log/log_test_requests.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.info("\n\n_____________________________new_log_____________________________")
logging.info(f"api: {api}\ntime_start: {time_start}\ntime_end: {time_end}\ntime_sleep: {time_sleep}\nresquests: {count_request}\nmessage: {message}")