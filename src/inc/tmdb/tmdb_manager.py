import logging, os, time, pathlib, threading
import tmdbsimple

from inc.logger.logger_setup import logger_setup

class TMDB_Manager:
# ==================================================================================================
    def search_movie(self, name):
        pass
# ==================================================================================================
    def search_tv(self, name):
        pass
# ==================================================================================================
    def list_scanner(self, id):
        self.tmdb_logger.info(f"Thread active: {self.tmdb_list_scanner_thread.name}")
        self.tv_list = self.tmdb_client.Lists(id=self.lists['tv'])
        self.movie_list = self.tmdb_client.Lists(id=self.lists['movies'])

        while True:
            self.tv_list_items = self.tv_list.info()
            self.movie_list_items = self.movie_list.info()

            for item in self.tv_list_items:
                pass
# ==================================================================================================
    def movie_details(self, id):
        pass
# ==================================================================================================
    def tv_show_details(self, id):
        pass
# ==================================================================================================
    def tv_season_details(self, id, season):
        pass
# ==================================================================================================
    def tv_episode_details(self, id, season, episode):
        pass
# ==================================================================================================
    def __init__(self, data, plm_path):
        self.logger_data = data['logger']
        self.api_key = data['api_key']
        self.lists = data['lists']

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
