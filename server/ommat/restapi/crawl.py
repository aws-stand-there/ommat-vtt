from flask import request
from flask import session
from flask_restful import Resource
from ommat.config import Config
from ommat.db import Database
from ommat.crawler import CrawlerThread

import json
import time

class Crawl(Resource):
    def get(self):
        timestamp = Database.get_crawler_timestamp()
        is_ongoing = Database.is_crawling_ongoing()
        return {
            'status': 0,
            "timestamp": timestamp,
            "is_ongoing": is_ongoing
        }

    def post(self):
        timestamp = Database.get_crawler_timestamp()
        now_timestamp = int(time.time())

        if Database.is_crawling_ongoing():
            return {'status': 1}
        else:
            thread = CrawlerThread(1, "CrawlJobTrigger", 1)
            thread.start()
            return {'status': 0}
        