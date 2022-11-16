import requests
import logging
import re
import time, datetime
import query
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from lxml import html




header={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'}
# comment

def crawl_out_post(link_cate, config, queue_cate_err):
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    list_data = []
    type_crawl = config['type_crawl']
    if type_crawl == 1:
        res = send_request(link_cate, type_crawl, param_scroll_down=False)
        lxml = html.fromstring(res.text, 'lxml')
        list_obj_cmt = detect_type(type_crawl, lxml, config['comment'])
        for obj in list_obj_cmt:
            comment = re.findall(r'\d+', obj.text_content())
            check_link_post = False
            while check_link_post == False:
                obj = obj.getparent()
                list_descendant = [node for node in obj]
                try:
                    for descendant in list_descendant:
                        full_text_node = html.tostring(descendant)
                        link_post = check_regex(config['link_post']['detect']['re'], [str(full_text_node)])
                        if link_post:
                            link_post = make_full_link(config['website'], link_post)
                            check_link_post = True
                            list_data.append({"type_doc":1, "datetime": datetime.datetime.now(), "resourceUrl":link_cate, "url":link_post[0], "comment":int(comment[0]) if len(comment) > 0 else "", "type":6})
                            break
                except:
                    queue_cate_err.put(link_cate)
                    pass
    elif type_crawl == 2:
        try:
            website = send_request(link_cate, type_crawl, param_scroll_down=True)
            list_obj_cmt = detect_type(type_crawl, website, config['comment'])
            for obj in list_obj_cmt:
                comment = re.findall(r'\d+', obj.get_attribute('textContent'))
                check_link_post = False
                while check_link_post == False:
                    obj = obj.find_element(By.XPATH, '..')
                    link_post = check_regex(config['link_post']['detect']['re'], [str(obj.get_attribute('innerHTML'))])
                    if link_post:
                        link_post = make_full_link(config['website'], link_post)
                        list_data.append({"type_doc":1, "datetime": datetime.datetime.now(), "resourceUrl":link_cate, "url":link_post[0], "comment":comment[0] if len(comment) > 0 else "", "type":6})
                        break
        except: # xảy ra khi time_out hoặc page không có data
            queue_cate_err.put(link_cate)
        finally:
            website.close()
    # list_data = check_replace_link(list_data)
    if len(list_data) > 0:
        # query.insert_col(col_temp_db, list_data)
        query.update_col(col_temp_db, list_data)
        return list_data
    else:
        pass
        # logging.info(f"not found data, url: {link_cate}")


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
            time.sleep(config_site['api']['time_sleep'])
            for api in list_api:
                try:
                    res = send_request(api, 1, param_scroll_down= False)
                    data = detect_responseType(config_site['comment_in_post']['responseType'], res)
                    try:
                        comment = check_regex(config_site['comment_in_post']['detect']['re'], [str(data)])[0]
                        comment = re.findall(r'\d+', comment)[0]
                        break
                    except: # xảy ra khi res.status_code() = 200 nhưng token hết hạn
                        comment = doc['comment']
                        # logging.info(f"412, api: {api}")
                except: # xảy ra khi res.status_code() = 403
                    # logging.info(f"res status:{res.status_code}, api: {api}")
                    comment = doc['comment']

                
    except:
        queue_post_err.put(doc)
        comment = 0

    return int(comment)


def send_request(link_cate, type_crawl, param_scroll_down):
    if type_crawl == 1:
        res = requests.get(link_cate, headers=header, timeout=10)
        return res
    elif type_crawl == 2:
        options = Options()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.headless = True
        browser = webdriver.Chrome(executable_path='./chrome_driver/chromedriver.exe', options=options)
        browser.implicitly_wait(10)
        browser.get(link_cate)
        scroll_down(browser, param_scroll_down)
        return browser


def get_id_post(link_post):
    id_post = re.findall(r'\d+', link_post)[-1]
    return id_post


def check_config(url):
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    list_web_config = col_config.find({})
    for config in list_web_config:
        domain = re.split('/|\\.', config['website'])[2]
        if domain in url:
            return config


def crawl_link_cate(config_site):
    for config_item in config_site['paging_1']:
        if config_item['type'] == 3:
            resp = requests.get(config_site['website'], headers=header, timeout=10)
            lxml = html.fromstring(resp.text, 'lxml')
            if config_item['value']['detect']['type'] == 1:
                list_link = lxml.xpath(config_item['value']['detect']['xpath'])
            if config_item['value']['detect']['type'] == 3:
                list_link = lxml.xpath(config_item['value']['detect']['xpath'])
                list_link = check_regex(config_item['value']['detect']['re'], list_link)
        elif config_item['type'] == 2:
                list_link = config_item['value']

    return make_full_link(config_site['website'], list_link)


def detect_responseType(response_type, res):
    if response_type == 1:
        return html.fromstring(res.text, 'lxml')
    elif response_type == 2:
        return res.json()


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


def detect_type(type_crawl, lxml, config):
    if type_crawl == 1:
        if config['detect']['type'] == 1:
            list_result = lxml.xpath(config['detect']['xpath'])
        elif config['detect']['type'] == 2:
            pass
        elif config['detect']['type'] == 3:
            list_result = lxml.xpath(config['detect']['xpath'])
            list_result = check_regex(config['detect']['re'], list_result)
            
    elif type_crawl == 2:
        list_result = lxml.find_elements(By.XPATH, config['detect']['xpath'])
    return list_result


def check_regex(regex, list_link):
    list_result = []
    for link in list_link:
        result = re.findall(regex, link)
        if result:
            list_result.append(result[0])
    return list(set(list_result))


def check_replace_link(list_data):
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    temp = []
    for doc in list_data:
        if col_temp_db.find_one({"url":doc['url']}):
            pass
        else:
            temp.append(doc)
    return temp


def make_full_link(url, list_link):
    for i in range(len(list_link)):
        if list_link[i].startswith('http') == False:
            if list_link[i].startswith('/'):
                if url.endswith('/'):
                    list_link[i] = url.rsplit('/', 1)[0] + list_link[i]
                else:
                    list_link[i] = url + list_link[i]
            else:
                if url.endswith('/'):
                    list_link[i] = url + list_link[i]
                else:
                    list_link[i] = url + "/" + list_link[i]
        else:
            pass
    return list_link

    
def scroll_down(browser, param_scroll_down):
    if param_scroll_down == True:
        speed = 70
        current_scroll_position, new_height= 0, 1
        while current_scroll_position <= new_height:
            current_scroll_position += speed
            browser.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
            new_height = browser.execute_script("return document.body.scrollHeight")
    else:
        pass
