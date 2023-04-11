import os, json, logging, time, threading, pathlib

from inc.logger.logger_setup import logger_setup
from inc.db.db_manager import DB_Manager
from inc.file.file_manager import File_Manager
from inc.plex.plex_manager import Plex_Manager
from inc.qbt.qbt_manager import QBT_Manager
from inc.tmdb.tmdb_manager import TMDB_Manager


class Plex_Library_Manager:
# ==================================================================================================
    def fetch_db_requests(self):
        self.plm_logger.info(f"Thread active: {self.fetch_db_requests_thread.name}")
        
        while True:
            
            time.sleep(1)
# ==================================================================================================
    def fetch_qbt_requests(self):
        self.plm_logger.info(f"Thread active: {self.fetch_qbt_requests_thread.name}")
        
        while True:
            
            time.sleep(1)
# ==================================================================================================
    def fetch_tmdb_requests(self):
        self.plm_logger.info(f"Thread active: {self.fetch_tmdb_requests_thread.name}")
        
        while True:
            db_request = self.TMDB_Manager.db_request
            qbt_request = self.TMDB_Manager.qbt_request

            if db_request['status'] == "new":
                self.TMDB_Manager.db_request['status'] = "processing"
                
                if db_request['operation'] == "search":
                    search_result = self.DB_Manager.search_entry(category=db_request['category'], query=db_request['data'])

                    if search_result != None:
                        self.TMDB_Manager.db_request['result'] = {"response": True}
                    elif search_result == None:
                        self.TMDB_Manager.db_request['result'] = {"response": False}
                    
            self.TMDB_Manager.db_request['status'] = "complete"
            
            if qbt_request['status'] == "new":
                self.TMDB_Manager.db_request['status'] = "processing"
                
                if qbt_request['operation'] == "add":
                    if qbt_request['data']['type'] == "Torrent":
                        action_result = self.QBT_Manager.modify_torrent(operation=qbt_request['operation'], category=qbt_request['category'], name=qbt_request['data']['name'])
                    elif qbt_request['data']['type'] == "RSS":
                        action_result = self.QBT_Manager.modify_rss_feed(operation=qbt_request['operation'], category=qbt_request['category'], name=qbt_request['data']['name'])
                elif qbt_request['operation'] == "remove":
                    action_result = self.QBT_Manager.modify_rss_feed(operation=qbt_request['operation'], category=qbt_request['category'], name=qbt_request['data']['name'])
                
                self.TMDB_Manager.qbt_request['result'] = action_result

            self.TMDB_Manager.qbt_request['status'] = "complete"

            time.sleep(1)
# ==================================================================================================
    def __init__(self):
        self.plm_path = os.getcwd()

        with open(self.plm_path+"/conf/config.json") as config_file:
            self.config = json.load(config_file)
        config_file.close()

        self.logger_data = self.config['plm_data']['logger']
        self.plm_logger = logger_setup(self.plm_path, self.logger_data)
        self.plm_logger.info(f"Config file read")

        self.DB_Manager = DB_Manager(self.config['db_data'], self.plm_path)
        self.plm_logger.info(f"New DB_Manager instance called")
        self.fetch_db_requests_thread = threading.Thread(target=self.fetch_db_requests, args=())
        try:
            self.fetch_db_requests_thread.start()
            self.plm_logger.info(f"Thread started: {self.fetch_db_requests_thread.name}")
        except:
            self.plm_logger.warning(f"Error starting thread: {self.fetch_db_requests_thread.name}")
        
        # self.File_Manager = File_Manager(self.config['file_data'], self.plm_path)
        # logging.info(f"New File_Manager instance called")
        
        # self.Plex_Manager = Plex_Manager(self.config['plex_data'], self.plm_path)
        # logging.info(f"New Plex_Manager instance called")
        
        self.QBT_Manager = QBT_Manager(self.config['qbt_data'], self.plm_path)
        self.plm_logger.info(f"New QBT_Manager instance called")
        self.fetch_qbt_requests_thread = threading.Thread(target=self.fetch_qbt_requests, args=())
        try:
            self.fetch_qbt_requests_thread.start()
            self.plm_logger.info(f"Thread started: {self.fetch_qbt_requests_thread.name}")
        except:
            self.plm_logger.warning(f"Error starting thread: {self.fetch_qbt_requests_thread.name}")
        
        self.TMDB_Manager = TMDB_Manager(self.config['tmdb_data'], self.plm_path)
        self.plm_logger.info(f"New TMDB_Manager instance called")
        self.fetch_tmdb_requests_thread = threading.Thread(target=self.fetch_tmdb_requests, args=())
        try:
            self.fetch_tmdb_requests_thread.start()
            self.plm_logger.info(f"Thread started: {self.fetch_tmdb_requests_thread.name}")
        except:
            self.plm_logger.warning(f"Error starting thread: {self.fetch_tmdb_requests_thread.name}")

PLM = Plex_Library_Manager()