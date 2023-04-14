import os, json, time, threading, pathlib

from inc.logger.loggerSetup import loggerSetup
from inc.db.dbManager import DBManager
from inc.file.fileManager import FileManager
from inc.plex.plexManager import PlexManager
from inc.qbt.qbtManager import QBTManager
from inc.rarbg.rarbgManager import RARBGManager
from inc.tmdb.tmdbManager import TMDBManager


class PlexLibraryManager:
# ==================================================================================================
    def fetchDBRequests(self):
        self.plmLogger.info(f"Thread active: {self.fdrThread.name}")
        
        while True:
            
            time.sleep(1)
# ==================================================================================================
    def fetchQBTRequests(self):
        self.plmLogger.info(f"Thread active: {self.fqrThread.name}")
        
        while True:
            
            time.sleep(1)
# ==================================================================================================
    def fetchTMDBRequests(self):
        self.plmLogger.info(f"Thread active: {self.ftrThread.name}")
        
        while True:
            dbRequest = self.TMDBManager.dbRequest
            qbtRequest = self.TMDBManager.qbtRequest

            if dbRequest['status'] == "new":
                self.TMDBManager.dbRequest['status'] = "processing"
                
                if dbRequest['operation'] == "search":
                    searchResult = self.DBManager.searchEntry(dbRequest['category'], dbRequest['data'])

                    if searchResult != None:
                        self.TMDBManager.dbRequest['result'] = {"response": True}
                    elif searchResult == None:
                        self.TMDBManager.dbRequest['result'] = {"response": False}
                    
            self.TMDBManager.dbRequest['status'] = "complete"
            
            if qbtRequest['status'] == "new":
                self.TMDBManager.dbRequest['status'] = "processing"
                
                if qbtRequest['operation'] == "add":
                    if qbtRequest['data']['type'] == "Torrent":
                        actionResult = self.QBTManager.modifyTorrent(operation=qbtRequest['operation'], category=qbtRequest['category'],
                                                                        name=qbtRequest['data']['name'])
                    elif qbtRequest['data']['type'] == "RSS":
                        actionResult = self.QBTManager.modifyRSSFeed(operation=qbtRequest['operation'], category=qbtRequest['category'],
                                                                         name=qbtRequest['data']['name'])
                elif qbtRequest['operation'] == "remove":
                    actionResult = self.QBTManager.modifyRSSFeed(operation=qbtRequest['operation'], category=qbtRequest['category'],
                                                                     name=qbtRequest['data']['name'])
                
                self.TMDBManager.qbtRequest['result'] = actionResult

            self.TMDBManager.qbtRequest['status'] = "complete"

            time.sleep(1)
# ==================================================================================================
    def __init__(self):
        self.plmPath = os.getcwd()

        with open(self.plmPath+"/conf/config.json") as configFile:
            self.config = json.load(configFile)
        configFile.close()

        self.loggerData = self.config['plmData']['logger']
        self.plmLogger = loggerSetup(self.plmPath, self.loggerData)
        self.plmLogger.info(f"Config file read")

        self.DBManager = DBManager(self.config['dbData'], self.plmPath)
        self.plmLogger.info(f"New DBManager instance called")
        self.fdrThread = threading.Thread(target=self.fetchDBRequests, args=())
        try:
            self.fdrThread.start()
            self.plmLogger.info(f"Thread started: {self.fdrThread.name}")
        except:
            self.plmLogger.warning(f"Error starting thread: {self.fdrThread.name}")
        
        # self.FileManager = FileManager(self.config['fileData'], self.plmPath)
        # logging.info(f"New FileManager instance called")
        
        # self.PlexManager = PlexManager(self.config['plexData'], self.plmPath)
        # logging.info(f"New PlexManager instance called")
        
        self.QBTManager = QBTManager(self.config['qbtData'], self.plmPath)
        self.plmLogger.info(f"New QBTManager instance called")
        self.fqrThread = threading.Thread(target=self.fetchQBTRequests, args=())
        try:
            self.fqrThread.start()
            self.plmLogger.info(f"Thread started: {self.fqrThread.name}")
        except:
            self.plmLogger.warning(f"Error starting thread: {self.fqrThread.name}")

        self.RARBGManager = RARBGManager(self.config['rarbgData'], self.plmPath)
        self.plmLogger.info(f"New RARBGManager instance called")
        
        self.TMDBManager = TMDBManager(self.config['tmdbData'], self.plmPath)
        self.plmLogger.info(f"New TMDBManager instance called")
        self.ftrThread = threading.Thread(target=self.fetchTMDBRequests, args=())
        try:
            self.ftrThread.start()
            self.plmLogger.info(f"Thread started: {self.ftrThread.name}")
        except:
            self.plmLogger.warning(f"Error starting thread: {self.ftrThread.name}")
# ==================================================================================================
PLM = PlexLibraryManager()