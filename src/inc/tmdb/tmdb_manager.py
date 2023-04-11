import os, time, pathlib, threading, datetime
import tmdbsimple

from inc.logger.logger_setup import logger_setup
from inc.requests.requests_bus import *

class TMDB_Manager:
# ==================================================================================================
    def list_scanner(self):
        self.tmdb_logger.info(f"Thread active: {self.tmdb_list_scanner_thread.name}")
        self.tv_list = self.tmdb_client.Lists(id=self.lists['tv']).info()
        self.movie_list = self.tmdb_client.Lists(id=self.lists['movies']).info()

        while True:
            self.tv_list_items = self.tv_list['items']
            self.movie_list_items = self.movie_list['items']
            self.tmdb_logger.info(f"Items fetched from lists: Movies (ID {self.lists['movies']}), TV (ID {self.lists['tv']})")

            for movie_item in self.movie_list_items:
                self.tmdb_logger.info(f"Sending request: search for entry with ID {movie_item['id']} in database")
                request_payload = {"operation": "search", "category": "Movies", "data": {"tmdb_id": movie_item['id']}}
                send_db_request(self, request_payload)

                self.tmdb_logger.info(f"Search result for database entry with ID {movie_item[id]}: {self.db_request['result']['response']}")
                if self.db_request['result']['response'] == True:
                    self.tmdb_logger.info(f"Sending request: delete RSS Feed for {movie_item['title']}")
                    request_payload = {"operation": "remove", "category": "Movies", "data": {"type": "RSS", "name": movie_item['title'].title()}}
                    send_qbt_request(self, request_payload)
                    self.qbt_request['result'] = {}
                elif self.db_request['result']['response'] == False:
                    current_date = datetime.datetime.today()
                    release_date = datetime.datetime.strptime(movie_item['release_date'], '%Y-%m-%d')
                    
                    if current_date < release_date:
                        self.tmdb_logger.info(f"Movie not yet released: {movie_item['title']} (release date {movie_item['release_date']})")
                        self.tmdb_logger.info(f"Sending request: add RSS Feed for {movie_item['title']}")
                        request_payload = {"operation": "add", "category": "Movies", "data": {"type": "RSS", "name": movie_item['title'].title()}}
                        send_qbt_request(self, request_payload)
                        self.qbt_request['result'] = {}
                    elif current_date > release_date:
                        self.tmdb_logger.info(f"Movie already released: {movie_item['title']} (release date {movie_item['release_date']})")
                        self.tmdb_logger.info(f"Sending request: try to add Torrent for {movie_item['title']}")
                        request_payload = {"operation": "add", "category": "Movies", "data": {"type": "Torrent", "name": movie_item['title'].title()}}
                        send_qbt_request(self, request_payload)
                        
                        if self.qbt_request['result']['response'] == "fail":
                            self.tmdb_logger.info(f"Torrent add failed: no suitable result")
                            self.tmdb_logger.info(f"Sending request: add RSS Feed for {movie_item['title']}")
                            request_payload = {"operation": "add", "category": "Movies", "data": {"type": "RSS", "name": movie_item['title'].title()}}
                            send_qbt_request(self, request_payload)
                            self.qbt_request['result'] = {}
                        elif self.qbt_request['result']['response'] == "success":
                            self.tmdb_logger.info(f"Torrent add successful: {movie_item['title']}")
                        self.qbt_request['result'] = {}
                self.db_request['result'] = {}

            for tv_item in self.tv_list_items:
                self.tmdb_logger.info(f"Sending request: search for entry with ID {tv_item['id']} in database")
                request_payload = {"operation": "search", "category": "TV", "data": {"tmdb_id": tv_item['id']}}
                send_db_request(self, request_payload)

                self.tmdb_logger.info(f"Search result for database entry with ID {tv_item['id']}: {self.db_request['result']['response']}")
                if self.db_request['result']['response'] == True:
                    self.tmdb_logger.info(f"Fetching details from TMDB: ID {tv_item['id']}")
                    tv_details = self.get_details(category="TV", id=tv_item['id'])
                    
                    production_status = tv_details['in_production']
                    last_air_date = datetime.datetime.strptime(tv_details['last_air_date'], '%Y-%m-%d')
                    week_delta = datetime.timedelta(days=7)
                    current_date = datetime.datetime.today()

                    self.tmdb_logger.info(f"TV Show in production: {tv_item['name']} -> {production_status}")
                    if production_status == False and current_date > last_air_date+week_delta:
                        self.tmdb_logger.info(f"TV Show last episode aired: over 1 week ago ({tv_item['name']} -> {tv_details['last_air_date']})")
                        self.tmdb_logger.info(f"Sending request: delete RSS Feed for {tv_item['name']}")
                        request_payload = {"operation": "remove", "category": "TV", "data": {"type": "RSS", "name": tv_item['name'].title()}}
                        send_qbt_request(self, request_payload)
                        self.qbt_request['result'] = {}
                    elif production_status == True or current_date < last_air_date+week_delta:
                        self.tmdb_logger.info(f"TV Show last episode aired: under 1 week ago: {tv_item['name']} -> {tv_details['last_air_date']}")
                        self.tmdb_logger.info(f"Sending request: add RSS Feed for episodes of {tv_item['name']}")
                        request_payload = {"operation": "add", "category": "TV", "data": {"type": "RSS", "name": tv_item['name'].title()}}
                        send_qbt_request(self, request_payload)
                        self.qbt_request['result'] = {}
                elif self.db_request['result']['response'] == False:
                    current_date = datetime.datetime.today()
                    first_air_date = datetime.datetime.strptime(tv_item['first_air_date'], '%Y-%m-%d')

                    if current_date < first_air_date:
                        self.tmdb_logger.info(f"TV Show not yet on air: {tv_item['name']} (first air date {tv_item['first_air_date']})")
                        self.tmdb_logger.info(f"Sending request: add RSS Feed for episodes of {tv_item['name']}")
                        request_payload = {"operation": "add", "category": "TV", "data": {"type": "RSS", "name": tv_item['name'].title()}}
                        send_qbt_request(self, request_payload)
                        self.qbt_request['result'] = {}
                    elif current_date > first_air_date:
                        self.tmdb_logger.info(f"TV Show already on air: {tv_item['name']} (first air date {tv_item['first_air_date']})")
                        self.tmdb_logger.info(f"Sending request: try to add Torrent for first episode of {tv_item['name']}")
                        request_payload = {"operation": "add", "category": "TV", "data": {"type": "Torrent", "name": tv_item['name'].title()}}
                        send_qbt_request(self, request_payload)

                        if self.qbt_request['result']['response'] == "fail":
                            self.tmdb_logger.info(f"Torrent add failed: no suitable result")
                            self.tmdb_logger.info(f"Sending request: add RSS Feed for episodes of {tv_item['name']}")
                            request_payload = {"operation": "add", "category": "TV Episode", "data": {"type": "RSS", "name": tv_item['name'].title()}}
                            send_qbt_request(self, request_payload)
                            self.qbt_request['result'] = {}
                        elif self.qbt_request['result']['response'] == "success":
                            self.tmdb_logger.info(f"Torrent add successfull: {tv_item['name']}")
                        self.qbt_request['result'] = {}
                    self.db_request['result'] = {}
# ==================================================================================================
    # def plm_db_request(self, operation, id, category):
    #     self.tmdb_logger.info(f"Sending new DB request to PLM: {operation}, {id}, {category}")
    #     self.db_request['operation'] = operation
    #     self.db_request['tmdb_id'] = id
    #     self.db_request['category'] = category
    #     self.db_request['status'] = "new"

    #     while self.db_request['status'] != "complete":
    #         time.sleep(0.5)

    #     self.tmdb_logger.info(f"DB request successfully completed: {self.db_request['result']}")
    #     self.db_request['status'] = "empty"
    #     self.db_request['operation'] = None
    #     self.db_request['tmdb_id'] = None
    #     self.db_request['category'] = None
# ==================================================================================================
    # def plm_qbt_request(self, operation, name, category):
    #     self.tmdb_logger.info(f"Sending new QBT request to PLM: {operation}, {name}, {category}")
    #     self.qbt_request['operation'] = operation
    #     self.qbt_request['name'] = name
    #     self.qbt_request['category'] = category
    #     self.qbt_request['status'] = "new"

    #     while self.qbt_request['status'] != "complete":
    #         time.sleep(0.5)

    #     self.tmdb_logger.info(f"QBT request successfully completed: {self.qbt_request['result']}")
    #     self.qbt_request['status'] = "empty"
    #     self.qbt_request['operation'] = None
    #     self.qbt_request['name'] = None
    #     self.qbt_request['category'] = None
# ==================================================================================================
    # def plm_rss_request(self, operation, name, category):
    #     self.tmdb_logger.info(f"Sending new RSS request to PLM: {operation}, {name}, {category}")
    #     self.rss_request['operation'] = operation
    #     self.rss_request['name'] = name
    #     self.rss_request['category'] = category
    #     self.rss_request['status'] = "new"

    #     while self.rss_request['status'] != "complete":
    #         time.sleep(0.5)

    #     self.tmdb_logger.info(f"RSS request successfully completed: {self.rss_request['result']}")
    #     self.rss_request['status'] = "empty"
    #     self.rss_request['operation'] = None
    #     self.rss_request['name'] = None
    #     self.rss_request['category'] = None
# ==================================================================================================
    def search(self, category, query):
        self.tmdb_logger.info(f"New TMDB {category} search order received: '{query}'")
        if category == "Movies":
            try:
                search_result = self.tmdb_client.Search().movie(query=query)
                self.tmdb_logger.info(f"{category} search order successful, sending results back to PLM")
            except:
                self.tmdb_logger.warning(f"Error executing {category} search order: '{query}'")
        elif category == "TV":
            try:
                search_result = self.tmdb_client.Search().tv(query=query)
                self.tmdb_logger.info(f"{category} search order successful, sending results back to PLM")
            except:
                self.tmdb_logger.warning(f"Error executing {category} search order: '{query}'")
        return search_result
# ==================================================================================================
    def get_details(self, category, id):
        self.tmdb_logger.info(f"New TMDB {category} details order received: ID {id}")
        if category == "Movies":
            try:
                details = self.tmdb_client.Movies(id=id).info()
                self.tmdb_logger.info(f"{category} details order successful, sending results back to PLM")
            except:
                self.tmdb_logger.warning(f"Error executing {category} details order: ID {id}")
        elif category == "TV":
            try:
                details = self.tmdb_client.TV(id=id).info()
                self.tmdb_logger.info(f"{category} details order sucessful, sending results back to PLM")
            except:
                self.tmdb_logger.warning(f"Error executing {category} details order: ID {id}")
        return details
# ==================================================================================================
    def __init__(self, data, plm_path):
        self.logger_data = data['logger']
        self.api_key = data['api_key']
        self.lists = data['lists']

        self.db_request = {"status": "empty", "operation": None, "category": None, "data": {}, "result": {}}
        self.qbt_request = {"status": "empty", "operation": None, "category": None, "data": {}, "result": {}}

        self.tmdb_logger = logger_setup(plm_path, self.logger_data)
        self.tmdb_logger.info(f"New TMDB_Manager instance created")

        try:
            self.tmdb_client = tmdbsimple
            self.tmdb_client.API_KEY = self.api_key
            self.tmdb_logger.info(f"TMDB_Client successfully created")
        except:
            self.tmdb_logger.warning(f"Error creating TMDB_Client")

        self.tmdb_list_scanner_thread = threading.Thread(target=self.list_scanner, args=())
        try:
            self.tmdb_list_scanner_thread.start()
            self.tmdb_logger.info(f"Thread started: {self.tmdb_list_scanner_thread.name}")
        except:
            self.tmdb_logger.warning(f"Error starting thread: {self.tmdb_list_scanner_thread.name}")
