import logging, os, time, pathlib, threading
import requests

from inc.logger.logger_setup import logger_setup

class TMDB_Manager:
# ==================================================================================================
    def __init__(self, data, plm_path):
        self.logger_data = data['logger']
        self.api_key = data['api_key']
        self.endpoints = data['endpoints']

        self.tmdb_logger = logger_setup(plm_path, self.logger_data)
        self.tmdb_logger.info(f"New TMDB_Manager instance created")