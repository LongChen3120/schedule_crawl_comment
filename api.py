from typing import Optional, List
from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks, Request, Body, Form, File, UploadFile, Query
from lxml import html
from bs4 import BeautifulSoup
import requests
import uvicorn

import crawl_cmt, query


app = FastAPI()

# ----- GET

# check data
@app.get('/check-comment-post')
def check_data(url:Optional[str] = Query(None)):
    comment = crawl_cmt.crawl_in_post(url, "")
    if url == None:
        return {
            "status_code":200,
            "message":"error url"
        }
    elif not comment:
        return {
            "status_code":404,
            "message":"can't find comment"
        }
    elif comment:
        return {
            "status_code":200,
            "link_post":url,
            "comment":comment
        }


@app.get('/check-comment-page')
def check_replace_img(url:Optional[str] = Query(None)):
    mycol_config, col_temp_db, mycol_today, mycol_1_day_before, mycol_2_day_before = query.connect_DB()
    website = url.split('/')[2]
    config_site = mycol_config.find_one({"website":{"$regex":f"{website}"}})
    if url == None:
        return {
            "status_code":200,
            "message":"error url"
        }
    elif not config_site:
        return{
            "status_code":404,
            "message":"not found config"
        }
    else:
        list_data = crawl_cmt.crawl_out_post(url, config_site)
        return{
            "status_code":200,
            "data":list_data
        }


if __name__ == "__main__":
    uvicorn.run("api:app", host="192.168.19.163", port=8000, reload=True)
    


