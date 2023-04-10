import logging, os, time, pathlib, threading
import plexapi

from inc.logger.logger_setup import logger_setup

class Plex_Manager:
# ==================================================================================================
    def __init__(self, data, plm_path):
        self.logger_data = data['logger']
        self.username = data['username']
        self.password = data['password']
        self.servername = data['servername']

        self.plex_logger = logger_setup(plm_path, self.logger_data)
        self.plex_logger.info(f"New Plex_Manager instance created")