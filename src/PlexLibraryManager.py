import os, json, time, threading, pathlib

from inc.logger.loggerSetup import loggerSetup
from inc.db.dbManager import DBManager
from inc.file.fileManager import FileManager
from inc.plex.plexManager import PlexManager
from inc.qbt.qbtManager import QBTManager
from inc.rarbg.rarbgManager import RARBGManager
from inc.tmdb.tmdbManager import TMDBManager


class PlexLibraryManager:
# Types of Requests
# {status, operation, category, data{}, response{result, }}
# DB
#   search: {new, search, TV/Movies, {id, seasonEpisode, savePath}, {found/not_found}}
#   add: {new, add, TV/Movies, {name, id, year (movies only), seasonEpisode (tv only), savePath}, {added/already_exists}}
#   update: {new, update, TV/Movies, {id, savePath}, {updated/not_found}}
#   remove: {new, remove, TV/Movies, {id, savePath}, {removed/not_found}}
# File:
#   organize: {new, organize, TV/Movies, {name}, {organized/not_found}}
# QBT:
#   add RSS: {new, add, TV Episode/TV Season/Movies, {type=RSS, name}, {added/failed/already_exists}}
#   add Torrent: {new, add, TV Episode/TV Season/Movies, {type=Torrent, magnet}, {added/failed}}
#   remove RSS: {new, remove, TV Episode/TV Season/Movies, {type=RSS, name} {removed/failed/not_found}}
#   remove Torrent: {new, remove, TV Episode/TV Season/Movies, {type=Torrent, hash}}
# RARBG:
#   search: {new, search, TV/Movies, {query, id}, {found/not_found, torrentData}}
# TMDB:
#   search: {new, search, TV/Movies, {name, year (movies only)}, {found/not_found, name, id, year (movies only)}}
#   details: {new, details, TV/Movies, {id}, {found/not_found, details}}
# 
# Requests done by:
#   File -> DB (update)
#   File -> DB (remove)
#   File -> QBT (add)
#   File -> TMDB (details)
#   QBT -> DB (add)
#   QBT -> File (organize)
#   QBT -> RARBG (search)
#   QBT -> TMDB (search)
#   TMDB -> DB (search)
#   TMDB -> QBT (add)
#   TMDB -> QBT (remove)

# ==================================================================================================
    def handleDBRequests(self, request):
        if request['operation'] == "search":
            result = self.DBManager.searchEntry(request['category'], request['data'])
        elif request['operation'] == "add" or request['operation'] == "update" or request['operation'] == "remove":
            result = self.DBManager.modifyEntry(request['operation'], request['category'], request['data'])
        
        return result
# ==================================================================================================
    def handleFileRequests(self, request):
        if request['operation'] == "organize":
            result = self.FileManager.triggerOrganize(request['category'], request['data'])
        
        return result
# ==================================================================================================
    def handleQBTRequests(self, request):
        if request['operation'] == "add" or request['operation'] == "remove":
            result = self.QBTManager.modifyTorrent(request['operation'], request['category'], request['data'])

        return result
# ==================================================================================================
    def handleRARBGRequests(self, request):
        if request['operation'] == "search":
            result = self.RARBGManager.searchTorrent(request['category'], request['data'])

        return result
# ==================================================================================================
    def handleTMDBRequests(self, request):
        if request['operation'] == "search":
            result = self.TMDBManager.searchItem(request['category'], request['data'])
        elif request['operation'] == "details":
            result = self.TMDBManager.detailsItem(request['category'], request['data'])

        return result
# ==================================================================================================
    def fetchFileRequests(self):
        self.plmLogger.info(f"Thread active: {self.ffrThread.name}")
        
        while True:
            dbRequest = self.FileManager.dbRequest
            qbtRequest = self.FileManager.qbtRequest

            if dbRequest['status'] == "new":
                self.FileManager.dbRequest['status'] = "processing"
                self.FileManager.dbRequest['result'] = self.handleDBRequests(dbRequest)
                self.FileManager.dbRequest['status'] = "complete"

            if qbtRequest['status'] == "new":
                self.FileManager.qbtRequest['status'] = "processing"
                self.FileManager.qbtRequest['result'] = self.handleQBTRequests(qbtRequest)
                self.FileManager.qbtRequest['status'] = "complete"
            
            time.sleep(1)
# ==================================================================================================
    def fetchQBTRequests(self):
        self.plmLogger.info(f"Thread active: {self.fqrThread.name}")
        
        while True:
            dbRequest = self.QBTManager.dbRequest
            fileRequest = self.QBTManager.fileRequest
            rarbgRequest = self.QBTManager.rarbgRequest
            tmdbRequest = self.QBTManager.tmdbRequest

            if dbRequest['status'] == "new":
                self.QBTManager.dbRequest['status'] = "processing"
                self.QBTManager.dbRequest['result'] = self.handleDBRequests(dbRequest)
                self.QBTManager.dbRequest['status'] = "complete"

            if fileRequest['status'] == "new":
                self.QBTManager.fileRequest['status'] = "processing"
                self.QBTManager.fileRequest['result'] = self.handleFileRequests(fileRequest)
                self.QBTManager.fileRequest['status'] = "complete"
            
            if rarbgRequest['status'] == "new":
                self.QBTManager.rarbgRequest['status'] = "processing"
                self.QBTManager.rarbgRequest['result'] = self.handleRARBGRequests(rarbgRequest)
                self.QBTManager.rarbgRequest['status'] = "complete"

            if tmdbRequest['status'] == "new":
                self.QBTManager.tmdbRequest['status'] = "processing"
                self.QBTManager.tmdbRequest['result'] = self.handleTMDBRequests(tmdbRequest)
                self.QBTManager.tmdbRequest['status'] = "complete"
            
            time.sleep(1)
# ==================================================================================================
    def fetchTMDBRequests(self):
        self.plmLogger.info(f"Thread active: {self.ftrThread.name}")
        
        while True:
            dbRequest = self.TMDBManager.dbRequest
            qbtRequest = self.TMDBManager.qbtRequest

            if dbRequest['status'] == "new":
                self.TMDBManager.dbRequest['status'] = "processing"
                self.TMDBManager.dbRequest['result'] = self.handleDBRequests(dbRequest)
                self.TMDBManager.dbRequest['status'] = "complete"
            
            if qbtRequest['status'] == "new":
                self.TMDBManager.qbtRequest['status'] = "processing"
                self.TMDBManager.qbtRequest['result'] = self.handleQBTRequests(qbtRequest)
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
        
        self.FileManager = FileManager(self.config['fileData'], self.plmPath)
        self.plmLogger.info(f"New FileManager instance called")
        self.ffrThread = threading.Thread(target=self.fetchFileRequests, args=())
        try:
            self.ffrThread.start()
            self.plmLogger.info(f"Thread started: {self.ffrThread.name}")
        except:
            self.plmLogger.warning(f"Error starting thread: {self.ffrThread.name}")
        
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