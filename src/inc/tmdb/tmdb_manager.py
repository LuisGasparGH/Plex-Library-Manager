import logging, os, time, pathlib, threading
import requests

class TMDB_Manager:
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
        self.tmdb_logger = logging.getLogger(logger_name)
        self.tmdb_logger.setLevel(logging.INFO)
        self.tmdb_logger.addHandler(handler)

    def __init__(self, data, plm_path):
        self.plm_path = plm_path
        self.logger_data = data['logger']
        self.api_key = data['api_key']
        self.endpoints = data['endpoints']

        self.logger_setup()
        self.tmdb_logger.info(f"New TMDB_Manager instance created")