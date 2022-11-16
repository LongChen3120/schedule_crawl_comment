import time
from threading import current_thread
from threading import get_ident
from threading import get_native_id
from concurrent.futures import ThreadPoolExecutor
 
# target task function
def work(value):
    time.sleep(5)
    # worker thread details
    print(5)
    thread = current_thread()
    print(f'Worker thread: name={thread.name}, idnet={get_ident()}, id={get_native_id()}')


def detect_time(ex):
    ex.map(work, range(5))
# entry point

def create_thread():
    with ThreadPoolExecutor(3) as executor:
        # submit some tasks
        detect_time(executor)
if __name__ == '__main__':
    # main thread details
    thread = current_thread()
    print(f'Main thread: name={thread.name}, idnet={get_ident()}, id={get_native_id()}')
    create_thread()