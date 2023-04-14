import os, time, pathlib, threading
import rarbgapi

from inc.logger.loggerSetup import loggerSetup

class RARBGManager:
# ==================================================================================================
    def searchAndAddTorrent(self, category):
        pass
# ==================================================================================================
    def __init__(self, data, plmPath):
        self.loggerData = data['logger']
        self.retries = data['retries']
        self.categories = data['categories']

        self.qbtRequest = {}

        self.rarbgLogger = loggerSetup(plmPath, self.loggerData)
        self.rarbgLogger.info(f"New RARBGManager instance created")

        try:
            retries = {'retries': self.retries}
            self.rarbgClient = rarbgapi.RarbgAPI(retries)
            self.rarbgLogger.info(f"rarbgClient successfully created")
        except:
            self.rarbgLogger.warning(f"Error creating rarbgClient")
