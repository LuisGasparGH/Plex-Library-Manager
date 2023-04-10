import logging, os, time, pathlib, threading
import pymongo

from inc.logger.logger_setup import logger_setup

class DB_Manager:
# ==================================================================================================
    # TO DO - Try and combine similar parts of update entry (mainly insert_one section)
    def update_movie_entry(self, name, save_path):
        self.db_logger.info(f"Request to update Movie entry received")
        self.tmdb_manager_request = {"status": "new", "name": name, "category": "Movies"}
        self.db_logger.info(f"New TMDB Movie search request sent to PLM: {self.tmdb_manager_request}")
        
        while self.tmdb_manager_request['status'] != "completed":
            time.sleep(0.5)
        
        result = self.tmdb_manager_request
        self.db_logger.info(f"Request successfully completed with result: {result}")
        
        self.tmdb_manager_request['status'] = "processing"
        movie_document = {"name": result['tmdb_name'], "tmdb_id": result['tmdb_id'], "save_path": save_path, "updated": False}
        
        try:
            self.movies_collection.insert_one(movie_document)
            self.db_logger.info(f"New Movie document inserted into {self.db.name}: {movie_document}")
        except:
            self.db_logger.warning(f"Error inserting Movie document into {self.db.name}: {movie_document}")

        self.tmdb_manager_request = {"status": "empty"}   
# ==================================================================================================
    def update_tv_entry(self, name, save_path, last_dl):
        self.db_logger.info(f"Request to update TV entry received")
        self.db_logger.info(f"Searching for TV entry in database with save path: {save_path}")
        entry_search = self.tv_collection.find_one({"save_path": save_path})

        if entry_search != None:
            self.db_logger.info(f"Entry found in {self.db.name}: {entry_search}")
            
            try:
                self.tv_collection.update_one({"_id": entry_search['_id']}, {"$set": {"last_dl": last_dl}})
                self.db_logger.info(f"Updated last download field for entry: {entry_search['name']}")
            except:
                self.db_logger.warning(f"Error updating entry in {self.db.name}: {entry_search}")
        elif entry_search == None:
            self.db_logger.info(f"Entry not found in {self.db.name}")
            self.tmdb_manager_request = {"status": "new", "name": name, "category": "TV"}
            self.db_logger.info(f"New TMDB TV search request sent to PLM: {self.tmdb_manager_request}")
            
            while self.tmdb_manager_request['status'] != "completed":
                time.sleep(0.5)
            
            result = self.tmdb_manager_request
            self.db_logger.info(f"Request successfully completed with result: {result}")
            
            self.tmdb_manager_request['status'] = "processing"
            tv_document = {"name": result['tmdb_name'], "tmdb_id": result['tmdb_id'], "save_path": save_path, "seasons": result['tmdb_seasons'], "last_dl": last_dl}
            
            try:
                self.movies_collection.insert_one(tv_document)
                self.db_logger.info(f"New TV document inserted into {self.db.name}: {tv_document}")
            except:
                self.db_logger.warning(f"Error inserting TV document into {self.db.name}: {tv_document}")

            self.tmdb_manager_request = {"status": "empty"}
# ==================================================================================================
    def __init__(self, data, plm_path):
        self.logger_data = data['logger']
        self.url = data['url']
        self.name = data['name']
        self.collections = data['collections']

        self.tmdb_manager_request = {"status": "empty"}

        self.db_logger = logger_setup(plm_path, self.logger_data)
        self.db_logger.info(f"New DB_Manager instance created")

        try:
            self.db_client = pymongo.MongoClient(self.url)
            self.db_logger.info(f"DB_Client successfully created")
        except:
            self.db_logger.warning(f"Error creating DB_Client with URL {self.url}")

        self.db = self.db_client[self.name]
        self.tv_collection = self.db[self.collections['tv']]
        self.movies_collection = self.db[self.collections['movies']]
        self.db_logger.info(f"Database and collections selected")

