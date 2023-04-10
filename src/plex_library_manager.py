import os, json, logging, time, threading, pathlib

from inc.db import DB_Manager
from inc.file import File_Manager
from inc.plex import Plex_Manager
from inc.qbt import QBT_Manager
from inc.tmdb import TMDB_Manager


class Plex_Library_Manager:
# ==================================================================================================
    # TEST VALID FOR ALL - LOGGER PATH NOT STARTING WITH "/"
    def logger_setup(self):
        logger_name = self.logger_data['name']
        logger_path = self.logger_data['path']
        try:
            handler = logging.FileHandler(self.plm_path+logger_path, mode='a')
        except:
            logger_dir = os.path.dirname(logger_path)
            os.makedirs(self.plm_path+logger_dir)
            handler = logging.FileHandler(self.plm_path+logger_path, mode='a')
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        self.plm_logger = logging.getLogger(logger_name)
        self.plm_logger.setLevel(logging.INFO)
        self.plm_logger.addHandler(handler)
# ==================================================================================================
    def qbt_manager_fetch_db_updates(self):
        self.plm_logger.info(f"Thread active: qbt_manager_fetch_db_updates")
        while True:
            while self.QBT_Manager.db_manager_update_entry['status'] != "new":
                time.sleep(60)
            db_entry = self.QBT_Manager.db_manager_update_entry

            if db_entry['category'] == "Movies":
                self.DB_Manager.update_movie_entry(name=db_entry['name'], save_path=db_entry['save_path'])
                self.QBT_Manager.db_manager_update_entry = {"status": "completed"}
            elif db_entry['category'] == "TV":
                self.DB_Manager.update_tv_entry(name=db_entry['name'], save_path=db_entry['save_path'], last_dl=db_entry['last_dl'])
                self.QBT_Manager.db_manager_update_entry = {"status": "completed"}
# ==================================================================================================
    def db_manager_fetch_tmdb_requests(self):
        self.plm_logger.info(f"Thread active: db_manager_fetch_tmdb_requests")
        while True:
            while self.DB_Manager.tmdb_manager_request['status'] != "new":
                time.sleep(60)
            tmdb_request = self.DB_Manager.tmdb_manager_request
            
            # TO DO - APPEND RESULT TO STATUS INSTEAD OF FULL COPY
            if tmdb_request['category'] == "Movies":
                result = self.TMDB_Manager.search_movie(name=tmdb_request['name'])
                self.DB_Manager.tmdb_manager_request = {"status": "completed", "tmdb_name": result['name'], "tmdb_id": result['id']}
            elif tmdb_request['category'] == "TV":
                result = self.TMDB_Manager.search_tv(name=tmdb_request['name'])
                self.DB_Manager.tmdb_manager_request = {"status": "completed", "tmdb_name": result['name'], "tmdb_id": result['id'], "tmdb_seasons": result['seasons']}
# ==================================================================================================
    def __init__(self):
        self.plm_path = os.getcwd()

        with open(self.plm_path+"/conf/config.json") as config_file:
            self.config = json.load(config_file)

        self.logger_data = self.config['plm_data']['logger']
        self.logger_setup()
        self.plm_logger.info(f"Config file read")

        self.DB_Manager = DB_Manager(self.config['db_data'], self.plm_path)
        logging.info(f"New DB_Manager instance called")
        self.db_manager_fetch_tmdb_requests_thread = threading.Thread(target=self.db_manager_fetch_tmdb_requests, args=())
        self.db_manager_fetch_tmdb_requests_thread.start()
        self.plm_logger.info(f"Thread started: db_manager_fetch_tmdb_requests")
        
        # self.File_Manager = File_Manager(self.config['file_data'], self.plm_path)
        # logging.info(f"New File_Manager instance called")
        
        # self.Plex_Manager = Plex_Manager(self.config['plex_data'], self.plm_path)
        # logging.info(f"New Plex_Manager instance called")
        
        self.QBT_Manager = QBT_Manager(self.config['qbt_data'], self.plm_path)
        self.plm_logger.info(f"New QBT_Manager instance called")
        self.qbt_manager_fetch_db_updates_thread = threading.Thread(target=self.qbt_manager_fetch_db_updates, args=())
        self.qbt_manager_fetch_db_updates_thread.start()
        self.plm_logger.info(f"Thread started: qbt_manager_fetch_db_updates")
        
        self.TMDB_Manager = TMDB_Manager(self.config['tmdb_data'], self.plm_path)
        logging.info(f"New TMDB_Manager instance called")

PLM = Plex_Library_Manager()