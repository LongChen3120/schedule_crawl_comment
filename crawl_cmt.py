import requests
import logging
import re
import json
import time, datetime
import query
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from lxml import html




header={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'}

def crawl_out_post(website, link_cate, config):
    col_config, col_temp_db, col_toppaper = query.connect_DB()
    type_crawl = config['type_crawl']
    browser = detect_type_crawl(config, link_cate)
    response = detect_type_response(browser, config)
    if type_crawl == 1:
        list_data = parse_html(response, website, link_cate, config)
    elif type_crawl == 2:
        list_data = parse_browser(response, website, link_cate, config)
    list_data = check_replace_link(list_data)
    if len(list_data) > 0:
        query.update_col(col_temp_db, list_data)
        query.insert_col(col_toppaper, list_data)
        return list_data
    else:
        print("not found data", link_cate)
        pass
        # logging.info(f"not found data, url: {link_cate}")


def crawl_in_post(doc):
    link_post = doc['url']
    config = check_config(link_post)
    type_crawl = config['crawl_detail']['type_crawl']
    if type_crawl == 1:
        try:
            config['crawl_detail']['api']
            id_post = get_id_post(link_post)
            comment = detect_type_api(id_post, config['crawl_detail'])
            return comment
        except:
            browser = detect_type_crawl(config['crawl_detail'], link_post)
            response = detect_type_response(browser, config['crawl_detail'])
            comment = html_find_xpath(response, config['crawl_detail']['detect_comment'])
            comment = detect_type_result(comment, config['crawl_detail']['detect_comment'])
            return comment
    elif type_crawl == 2:
        pass


def detect_type_crawl(config, url):
    if config['type_crawl'] == 1:
        try:
            res = requests.get(url, headers=header, timeout=10)
            return res
        except:
            logging.info("exception:", exc_info=True)
    elif config['type_crawl'] == 2:
        try:
            options = Options()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.headless = True
            browser = webdriver.Chrome(executable_path='./chrome_driver/chromedriver.exe', options=options)
            browser.implicitly_wait(10)
            browser.get(url)
            return browser
        except:
            logging.info("exception:", exc_info=True)


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


def crawl_link_cate(config):
    browser = detect_type_crawl(config, config['url'])
    response = detect_type_response(browser, config)
    list_link_cate = detect_type_result(html_find_xpath(response, config['detect_link_cate']), config['detect_link_cate'])
    return make_full_link(config['url'], list_link_cate)


def detect_type_response(browser, config):
    if config['type_response'] == 1:
        response = html.fromstring(browser.text, 'lxml')
        return response
    elif config['type_response'] == 2:
        response = browser.json()
        return response
    elif config['type_response'] == 3:
        return browser


def detect_type_api(id_post, config):
    if config['api']['type_api'] == 1:
        api, list_api = detect_type_param(config['api']['url'], id_post, config['api'])
        if len(list_api) == 0:
            browser = detect_type_crawl(config, api)
            response = detect_type_response(browser, config)
            comment = parse_json(response, config)
            return comment
        else:
            max_comment = 0
            for api in list_api:
                browser = detect_type_crawl(config, api)
                response = detect_type_response(browser,config)
                comment = parse_json(response, config)
                if comment <= max_comment:
                    continue
                else:
                    max_comment = comment
                    break
            return max_comment
    elif config['api']['type_api'] == 2:
        payload = config['api']['data']
        payload, list_api = detect_type_param(str(payload), id_post, config['api'])
        browser = requests.post(config['api']['url'], headers=header, data=eval(payload), timeout=10)
        response = detect_type_response(browser, config)
        comment = parse_json(response, config)  
        return comment


def parse_html(response, website, resourceUrl, config):
    list_data = []
    list_obj_cmt = detect_type_result(html_find_xpath(response, config['detect_comment']), config['detect_comment'])
    for obj in list_obj_cmt:
        comment = re.findall(r'\d+', obj.text_content())
        check_link_post = False
        while comment and check_link_post == False:
            obj = obj.getparent()
            list_descendant = [node for node in obj.iterdescendants()]
            try:
                for descendant in list_descendant:
                    link_post = html_find_xpath(descendant, config['detect_link'])
                    if not link_post:
                        continue
                    link_post = detect_type_result(link_post, config['detect_link'])
                    if link_post:
                        link_post = make_full_link(website, [link_post])
                        check_link_post = True
                        list_data.append(
                            {
                                "type_doc":1, 
                                "datetime": datetime.datetime.now(), 
                                "resourceUrl":resourceUrl, "url":link_post[0], 
                                "comment":int(comment[0]), 
                                "type":6
                                }
                        )
                        break
            except:
                pass
    return list_data


def parse_browser(response, website, resourceUrl, config):
    list_data = []
    try:
        list_obj_cmt = response.find_elements(By.XPATH, config['detect_comment']['xpath'])
        for obj in list_obj_cmt:
            comment = re.findall(r'\d+', obj.get_attribute('textContent'))
            check_link_post = False
            while comment and check_link_post == False:
                obj = obj.find_element(By.XPATH, '..')
                link_post = check_regex(config['detect_link']['re'], [str(obj.get_attribute('innerHTML'))])
                if link_post:
                    link_post = make_full_link(website, link_post)
                    list_data.append({"type_doc":1, "datetime": datetime.datetime.now(), "resourceUrl":resourceUrl, "url":link_post[0], "comment":int(comment[0]), "type":6})
                    break
    except: # xảy ra khi time_out hoặc page không có data
        pass
    finally:
        response.close()
    return list_data

def parse_json(response, config):
    new_obj = get_all_key_json(response, {})
    try:
        return new_obj[config['detect_comment']['key']]
    except:
        return 0
    

def get_all_key_json(obj, new_obj):
    for key, vals in obj.items():
        if isinstance(vals, str):
            new_obj[key] = vals
        elif isinstance(vals, int):
            new_obj[key] = vals
        elif isinstance(vals, dict):
            get_all_key_json(vals, new_obj)
        elif isinstance(vals, list):
            for temp in vals:
            # for k, v in vals.items():
                get_all_key_json(temp, new_obj)
        else:
            new_obj[key] = ""
    return new_obj


def detect_type_result(result, config):
    try:
        type_result = config['type_result'] 
        if type_result == 1:
            return elements_to_output(result, config)
        elif type_result == 2:
            return list_string_to_output(result, config)
        elif type_result == 3:
            return list_int_to_output(result, config)
        elif type_result == 4:
            return string_to_output(result, config)
        elif type_result == 5:
            return int_to_output(result, config)
        elif type_result == 6:
            return datetime_to_output(result, config)
        elif type_result == 7:
            return timestamp_to_output(result, config)
    except:
        return config


def elements_to_output(obj, config):
    if config['type_output'] == 1: 
        return obj
    elif config['type_output'] == 2:
        pass
    elif config['type_output'] == 3:
        pass
    elif config['type_output'] == 4:
        string = detect_type_find(remove_space("".join(obj)).strip(), config)
        return string
    elif config['type_output'] == 5:
        pass
    elif config['type_output'] == 6:
        pass
    pass


def html_find_xpath(browser, config):
    try:
        return browser.xpath(config['xpath'])
    except:
        return ""


def list_string_to_output(obj, config):
    if config['type_output'] == 2:
        list_output = []
        for i in obj:
            result = detect_type_find(i, config)
            list_output.append(result)
        return list_output
    elif config['type_output'] == 3:
        list_numb = detect_type_find(remove_space("".join(obj)).strip(), config)
        return [int(i) for i in list_numb]
    elif config['type_output'] == 4:
        string = detect_type_find(remove_space("".join(obj)).strip(), config)
        return "".join(string)
    elif config['type_output'] == 5:
        numb = detect_type_find(remove_space("".join(obj)).strip(), config)
        return int(numb)
    elif config['type_output'] == 6:
        time = detect_type_find(remove_space("".join(obj)).strip(), config)
        return detect_time_format(time, config)


def list_int_to_output(obj, config):
    pass


def string_to_output(obj, config):
    if config['type_output'] == 3:
        obj = detect_type_find(remove_space("".join(obj).strip()), config)
        return [int(i) for i in obj]
    elif config['type_output'] == 4:
        obj = detect_type_find(remove_space("".join(obj)).strip(), config)
        return obj
    elif config['type_output'] == 5:
        obj = detect_type_find(remove_space("".join(obj)).strip(), config)
        return int(obj[0]) if isinstance(obj, list) else int(obj)
    elif config['type_output'] == 2:
        pass
    elif config['type_output'] == 6:
        obj = detect_type_find(remove_space("".join(obj)).strip(), config)
        time = detect_time_format(obj, config)


def int_to_output(obj, config):
    if config['type_output'] == 5:
        return obj
    elif config['type_output'] == 2:
        pass
    elif config['type_output'] == 3:
        pass
    elif config['type_output'] == 4:
        pass
    elif config['type_output'] == 6:
        pass


def datetime_to_output(obj, config):
    pass


def timestamp_to_output(obj, config):
    if config['type_output'] == 6:
        obj = detect_type_find(obj, config)[0]
        obj = datetime.datetime.fromtimestamp(int(obj)/1000)
        return obj
    elif config['type_output'] == 3:
        pass
    elif config['type_output'] == 4:
        pass
    elif config['type_output'] == 5:
        pass
    elif config['type_output'] == 2:
        pass


def detect_type_find(obj, config):
    if config['type_find'] == 1: # giữ nguyên obj
        return obj
    elif config['type_find'] == 2: # tìm theo regex
        return regex_extract(obj, config)


def regex_extract(obj, config):
    regex = config['re']
    result = re.findall(regex, obj)
    return result


def detect_time_format(time, config):
    if type(time) == list:
        time = time[0]
    time_format = config['time_format'].replace("days","%d").replace("months","%m").replace("years","%Y").replace("hours","%H").replace("minutes","%M").replace("seconds","%S").replace("microseconds", "%f")
    time = datetime.datetime.strptime(time, time_format)
    try:
        params = config['replace'].split('=')
        if params[0] == "years":
            time = time.replace(year=int(params[1]))
        elif params[0] == "months":
            time = time.replace(month=int(params[1]))
        elif params[0] == "days":
            time = time.replace(day=int(params[1]))
        elif params[0] == "hours":
            time = time.replace(hour=int(params[1]))
    except:
        pass
    return time


def remove_space(string):
    return re.sub('\s+', ' ', string)


def detect_type_param(string, id_post, config):
    list_string = []
    for param in config['params']:
        if param['type_replace'] == 1:
            new_string = string.replace(param['old_val'], id_post)
        elif param['type_replace'] == 2:
            for val in param['new_val']:
                list_string.append(new_string.replace(param['old_val'], val))
    return new_string, list_string


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
    list_link_check = []
    for doc in list_data:
        url = doc['url']
        if col_temp_db.find_one({"url":url}) and url in list_link_check:
            pass
        else:
            temp.append(doc)
            list_link_check.append(url)
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
