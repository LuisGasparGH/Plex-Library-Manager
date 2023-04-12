import logging, os, time, pathlib, threading
import plexapi

from inc.logger.loggerSetup import loggerSetup

class PlexManager:
# ==================================================================================================
    def __init__(self, data, plmPath):
        self.loggerData = data['logger']
        self.username = data['username']
        self.password = data['password']
        self.servername = data['servername']

        self.plexLogger = loggerSetup(plmPath, self.loggerData)
        self.plexLogger.info(f"New PlexManager instance created")