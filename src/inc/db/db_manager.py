import logging, os, time, pathlib, threading
import pymongo

class DB_Manager:
# ==================================================================================================
    def logger_setup(self, logger_data):
        logger_name = logger_data['name']
        logger_path = logger_data['path']
        try:
            handler = logging.FileHandler(self.plm_path+logger_path, mode='a')
        except:
            logger_dir = os.path.dirname(logger_path)
            os.makedirs(self.plm_path+logger_dir)
            handler = logging.FileHandler(self.plm_path+logger_path, mode='a')
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        self.db_logger = logging.getLogger(logger_name)
        self.db_logger.setLevel(logging.INFO)
        self.db_logger.addHandler(handler)
# ==================================================================================================
    def update_movie_entry(self, name, save_path):
        self.tmdb_manager_request = {"status": "new", "name": name, "category": "Movies"}
        self.db_logger.info(f"New TMDB Movie search request sent to PLM: {self.tmdb_manager_request}")
        while self.tmdb_manager_request['status'] != "completed":
            time.sleep(0.5)
        result = self.tmdb_manager_request
        self.db_logger.info(f"Request successfully completed with result: {result}")
        self.tmdb_manager_request['status'] = "empty"
        movie_document = {"name": result['tmdb_name'], "tmdb_id": result['tmdb_id'], "save_path": save_path, "updated": False}
        self.movies_collection.insert_one(movie_document)
        self.db_logger.info(f"New Movie document inserted into {self.db.name}: {movie_document}")   
# ==================================================================================================
    def update_tv_entry(self, name, save_path, last_dl):
        self.db_logger.info(f"Searching for TV entry in database with save path: {save_path}")
        entry_search = self.db_client.find({"save_path": save_path})
        if len(entry_search) != 0:
            self.tv_collection.update_one({"save_path": save_path}, {"$set": {"last_dl": last_dl}})
            self.db_logger.info(f"Entry found in {self.db.name}, updated last download")
        elif len(entry_search) == 0:
            self.db_logger.info(f"Entry not found in {self.db.name}")
            self.tmdb_manager_request = {"status": "new", "name": name, "category": "TV"}
            self.db_logger.info(f"New TMDB TV search request sent to PLM: {self.tmdb_manager_request}")
            while self.tmdb_manager_request['status'] != "completed":
                time.sleep(0.5)
            result = self.tmdb_manager_request
            self.db_logger.info(f"Request successfully completed with result: {result}")
            self.tmdb_manager_request['status'] = "empty"
            tv_document = {"name": result['tmdb_name'], "tmdb_id": result['tmdb_id'], "save_path": save_path, "seasons": result['tmdb_seasons'], "last_dl": last_dl}
            self.movies_collection.insert_one(tv_document)
            self.db_logger.info(f"New TV document inserted into {self.db.name}: {tv_document}")
# ==================================================================================================
    def __init__(self, data, plm_path):
        self.plm_path = plm_path
        self.logger_data = data['logger']
        self.url = data['url']
        self.name = data['name']
        self.collections = data['collections']

        self.tmdb_manager_request = {"status": "empty"}

        self.logger_setup()
        self.db_logger.info(f"New DB_Manager instance created")

        self.db_client = pymongo.MongoClient(self.url)
        self.db_logger.info(f"Client created")
        self.db = self.db_client[self.name]
        self.tv_collection = self.db[self.collections['tv']]
        self.movies_collection = self.db[self.collections['movies']]
        self.db_logger.info(f"Database and collections selected")

