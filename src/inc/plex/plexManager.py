import os, time, pathlib, threading
from plexapi.myplex import MyPlexAccount

from inc.logger.loggerSetup import loggerSetup

class PlexManager:
# ==================================================================================================
    def watchedScanner(self):
        self.plexLogger.info(f"Thread active: {self.scannerThread.name}")

        while True:
            self.watchedMovies = self.serverClient.library.section('Movies').search(watched=True)
            self.watchedTV = self.serverClient.library.section('TV Shows').search(watched=True)
            
            time.sleep(86400)
            pass
# ==================================================================================================
    def __init__(self, data, plmPath):
        self.loggerData = data['logger']
        self.username = data['username']
        self.password = data['password']
        self.servername = data['servername']

        self.fileRequest = {}

        self.plexLogger = loggerSetup(plmPath, self.loggerData)
        self.plexLogger.info(f"New PlexManager instance created")

        try:
            self.accountClient = MyPlexAccount(self.username, self.password)
            self.plexLogger.info(f"accountClient successfully created")
            try:
                self.serverClient = self.accountClient.resource(self.servername).connect()
                self.plexLogger.info(f"Successfully connected to serverClient")
            except:
                self.plexLogger.warning(f"Error connecting to serverClient")
        except:
            self.plexLogger.warning(f"Error creating accountClient")

        self.scannerThread = threading.Thread(target=self.watchedScanner, args=())
        try:
            self.scannerThread.start()
            self.plexLogger.info(f"Thread started: {self.scannerThread.name}")
        except:
            self.plexLogger.warning(f"Error starting thread: {self.scannerThread.name}")
