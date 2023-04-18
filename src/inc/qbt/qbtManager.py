import time, pathlib, threading, re, datetime
import qbittorrentapi

from inc.logger.loggerSetup import loggerSetup
from inc.requests.requestsBus import *

class QBTManager:
# ==================================================================================================
    def torrentScanner(self):
        self.qbtLogger.info(f"Thread active: {self.scannerThread.name}")
        
        while True:
            #------------------------------------------------------------------------------------------------------
            # STEP 0 - Detects paused and seeding torrents
            paused = self.qbtClient.torrents_info("paused")
            seeding = self.qbtClient.torrents_info("seeding")
            
            if len(paused) != 0:
                self.qbtLogger.info(f"Paused torrents found: {len(paused)}")
                
                for torrent in paused:
                    if torrent.category != "Movies" and torrent.category != "TV Episode" and torrent.category != "TV Season":
                        self.qbtLogger.warning(f"Incompatible category detected: {torrent.category}, on torrent {torrent.name}, please review manually")
                        continue
                    
                    self.qbtLogger.info(f"Handling paused {torrent.category} torrent: {torrent.name}")
                    # Gets files from torrent
                    torrentFiles = self.qbtClient.torrents_files(torrent.hash)
                    filteredFiles = []
                    #------------------------------------------------------------------------------------------------------
                    # STEP 1 - Deletes all non media torrent files
                    for file in torrentFiles:
                        fileExt = pathlib.Path(file.name).suffix

                        if fileExt not in self.mediaExt:
                            try:
                                self.qbtClient.torrents_file_priority(torrent.hash, file.id, 0)
                                self.qbtLogger.info(f"Non-media file removed from {torrent.name}: {file.name}")
                            except:
                                self.qbtLogger.warning(f"Error removing non-media file from {torrent.name}: {file.name}")
                        elif fileExt in self.mediaExt:
                            filteredFiles.append(file)
                    #------------------------------------------------------------------------------------------------------
                    # STEP 2 - Filters item name
                    # For Movies:
                    if torrent.category == "Movies":
                        for pattern in self.movieRegex:
                            year = re.findall(pattern, filteredFiles[0].name, re.IGNORECASE)
                            if len(year) != 0:
                                break

                        if len(year) != 0:
                            self.qbtLogger.info(f"Regex correspondence found for {torrent.name} torrent: {year}")
                        elif len(year) == 0:
                            self.qbtLogger.warning(f"No regex correspondence found for {torrent.name}, please review manually")
                            break

                        itemName = filteredFiles[0].name.split(year[0])[0].title()
                        year = year[0].replace(" ", "")
                        year = year.replace(".", "")
                        self.qbtLogger.info(f"Details from {torrent.name}: Title - {itemName}, Year - {year}")
                    #------------------------------------------------------------------------------------------------------
                    # For TV Shows:
                    elif torrent.category == "TV Episode" or torrent.category == "TV Season":
                        for pattern in self.tvRegex:
                            epName = re.findall(pattern, file.name, re.IGNORECASE)
                            if len(epName) != 0:
                                break

                        if len(epName) != 0:
                            self.qbtLogger.info(f"Regex correspondence found for {torrent.name} torrent: {epName}")
                        elif len(epName) == 0:
                            self.qbtLogger.warning(f"No regex correspondence found for {torrent.name}, please review manually")

                        itemName = file.name.split(epName[0])[0].title()
                        epName = epName[0].replace(" ", "")
                        epName = epName.replace(".", "").title()
                        season = epName[0:3]
                        self.qbtLogger.info(f"Details from {torrent.name}: Title - {itemName}, Season - {season}")
                    #------------------------------------------------------------------------------------------------------
                    # STEP 3 - Makes request to TMDB to search for item
                    # For Movies:
                    if torrent.category == "Movies":
                        requestPayload = {"operation": "search", "category": "Movies", "data":{"name": itemName, "year": year}}
                        self.qbtLogger.info(f"Sending TMDB request: {requestPayload}")

                        sendTMDBRequest(self, requestPayload)
                        self.qbtLogger.info(f"TMDB request completed with response: {self.tmdbRequest['response']}")
                        
                        if self.tmdbRequest['response']['result'] == "found":
                            tmdbName = self.tmdbRequest['response']['name']
                            tmdbId = self.tmdbRequest['response']['id']
                            tmdbYear = self.tmdbRequest['response']['year']
                            savePath = "/downloads/Movies/" + tmdbName
                            
                            requestPayload = {"operation": "add", "category": "Movies",
                                              "data":{"name": tmdbName,
                                                      "id": tmdbId,
                                                      "year": tmdbYear,
                                                      "savePath": savePath}}
                            
                            sendDBRequest(self, requestPayload)
                            self.qbtLogger.info(f"DB request completed with response: {self.dbRequest['response']}")

                            if self.dbRequest['response']['result'] == "alreadyExists":
                                self.modifyTorrent("remove", {"hash": torrent.hash})
                                self.qbtLogger.info(f"Removed already existing {torrent.category} torrent: {torrent.name}")

                                self.modifyRSSFeed("remove", {"name": tmdbName})
                                self.qbtLogger.info(f"Removed {torrent.category} RSS feed: {tmdbName}")
                        elif self.tmdbRequest['response']['result'] == "notFound":
                            torrentName = torrent.name + ".MANUAL_REVIEW"
                            self.qbtClient.torrents_rename(torrent.hash, torrentName)

                            self.qbtLogger.warning(f"TMDB result not found, renamed torrent: {torrent.name} -> {torrentName}, please review manually")
                            break
                    #------------------------------------------------------------------------------------------------------
                    # For TV Shows:
                    elif torrent.category == "TV Episode" or torrent.category == "TV Season":
                        requestPayload = {"operation": "search", "category": "TV", "data":{"name": itemName}}
                        self.qbtLogger.info(f"Sending TMDB request: {requestPayload}")

                        sendTMDBRequest(self, requestPayload)
                        self.qbtLogger.info(f"TMDB request completed with response: {self.tmdbRequest['response']}")

                        if self.tmdbRequest['response']['result'] == "found":
                            tmdbName = self.tmdbRequest['response']['name']
                            tmdbId = self.tmdbRequest['response']['id']
                            savePath = "/downloads/TV Shows/" + tmdbName + "/" + season

                            for file in filteredFiles:
                                removedFiles = 0
                                requestPayload = {"operation": "add", "category": "TV",
                                                "data":{"name": tmdbName,
                                                        "id": tmdbId,
                                                        "seasonEpisode": epName,
                                                        "savePath": savePath}}
                                
                                sendDBRequest(self, requestPayload)
                                self.qbtLogger.info(f"DB request completed with response: {self.dbRequest['response']}")

                                if self.dbRequest['response']['result'] == "alreadyExists":
                                    self.qbtClient.torrents_file_priority(torrent.hash, file.id, 0)
                                    self.qbtLogger.info(f"Removed file from torrent: {file.name} (already exists)")
                                    removedFiles += 1

                            if removedFiles == len(filteredFiles):
                                self.modifyTorrent("remove", {"hash": torrent.hash})
                                self.qbtLogger.info(f"Removed already existing {torrent.category} torrent: {torrent.name}")
                                
                                rssFeedExists = self.modifyRSSFeed("search", "TV", tmdbName)

                                if rssFeedExists['response'] == "found":
                                    requestPayload = {"operation": "details", "category": "TV",
                                                      "data":{"id": tmdbId,}}
                                    
                                    sendTMDBRequest(self, requestPayload)
                                    self.qbtLogger.info(f"TMDB request completed with response: {self.tmdbRequest['response']}")

                                    if self.tmdbRequest['response']['result'] == "found":
                                        productionStatus = self.tmdbRequest['response']['productionStatus']
                                        currentDate = datetime.datetime.today()
                                        lastAirDate = datetime.datetime.strptime(self.tmdbRequest['response']['lastAirDate'])
                                        weekDelta = datetime.timedelta(days=7)

                                        if productionStatus == False and currentDate > lastAirDate+weekDelta:
                                            self.modifyRSSFeed("remove", {"name": tmdbName})
                                            self.qbtLogger.info(f"Removed {torrent.category} RSS feed: {tmdbName}")
                        elif self.tmdbRequest['response']['result'] == "notFound":
                            torrentName = torrent.name + ".MANUAL_REVIEW"
                            self.qbtClient.torrents_rename(torrent.hash, torrentName)

                            self.qbtLogger.warning(f"TMDB result not found: renamed torrent: {torrent.name} -> {torrentName}, please review manually")
                    #------------------------------------------------------------------------------------------------------
                    # STEP 4 - Renames torrent and media files
                    # For Movies:
                    if torrent.category == "Movies":
                        torrentName = tmdbName + "." + tmdbYear

                        for file in filteredFiles:
                            fileName = torrentName + fileExt
                            try:
                                self.qbtClient.torrents_rename_file(torrent.hash, file.id, file.name, fileName)
                                self.qbtLogger.info(f"Media file renamed in {torrent.name}: {file.name} -> {fileName}")
                            except:
                                self.qbtLogger.warning(f"Error renaming media file in {torrent.name}: {file.name}")

                        self.qbtClient.torrents_rename(torrent.hash, torrentName)
                        self.qbtLogger.info(f"Torrent of {torrent.category} category renamed: {torrent.name} -> {torrentName}")
                    elif torrent.category == "TV Episode" or torrent.category == "TV Season":
                        torrentName = tmdbName + "." + season

                        for file in filteredFiles:
                            fileName = tmdbName + "." + epName
                            try:
                                self.qbtClient.torrents_rename_file(torrent.hash, file.id, file.name, fileName)
                                self.qbtLogger.info(f"Media file renamed in {torrent.name}: {file.name} -> {fileName}")
                            except:
                                self.qbtLogger.warning(f"Error renaming media file in {torrent.name}: {file.name}")

                        self.qbtClient.torrents_rename(torrent.hash, torrentName)
                        self.qbtLogger.info(f"Torrent of {torrent.category} category renamed: {torrent.name} -> {torrentName}")
                    #------------------------------------------------------------------------------------------------------
                    # STEP 5 - Change save path
                    # For Movies:
                    if torrent.category == "Movies":
                        try:
                            self.qbtClient.torrents_set_save_path(savePath, torrent.hash)
                            self.qbtLogger.info(f"Save path changed in {torrent.name}: {torrent.save_path} -> {savePath}")
                        except:
                            self.qbtLogger.warning(f"Error changing save path: {torrent.name}")
                    elif torrent.category == "TV Episode" or torrent.category == "TV Season":
                        try:
                            self.qbtClient.torrents_set_save_path(savePath, torrent.hash)
                            self.qbtLogger.info(f"Save path changed in {torrent.name}: {torrent.save_path} -> {savePath}")
                        except:
                            self.qbtLogger.warning(f"Error changing save path: {torrent.name}")
                    #------------------------------------------------------------------------------------------------------
                    # STEP 6 - Resume torrent
                    try:
                        self.qbtClient.torrents_resume(torrent.hash)
                        self.qbtLogger.info(f"Torrent resumed: {torrentName}")
                    except:
                        self.qbtLogger.warning(f"Error resuming torrent: {torrentName}")
            #------------------------------------------------------------------------------------------------------
            if len(seeding) != 0:
                self.qbtLogger.info(f"Seeding torrents found: {len(seeding)}")
                for torrent in seeding:
                    try:
                        self.qbtClient.torrents_delete(False, torrent.hash)
                        self.qbtLogger.info(f"Deleted seeding torrent: {torrent.name}")
                    except:
                        self.qbtLogger.warning(f"Error deleting seeding torrent: {torrent.name}")
            
            time.sleep(3600)
# ==================================================================================================
    def modifyTorrent(self, operation, data):
        if operation == "add":
            opResult = self.qbtClient.torrents_add(data['magnet'])

            if opResult == "Ok.":
                self.qbtLogger.info(f"Torrent added successfully: {data}")
                
                actionResult = {"response": "added"}
            elif opResult == "Fails.":
                self.qbtLogger.warning(f"Error adding torrent: {data}")

                actionResult = {"response": "failed"}
        elif operation == "remove":
            try:
                opResult = self.qbtClient.torrents_delete(False, data['hash'])
                self.qbtLogger.info(f"Torrent removed successfully: {data}")

                actionResult = {"response": "removed"}
            except:
                self.qbtLogger.warning(f"Error removing torrent: {data}")

                actionResult = {"response": "failed"}

        return actionResult
# ==================================================================================================
    def modifyRSSFeed(self, operation, category, name):
        # Apply logger
        rssRules = self.qbtClient.rssRules()
        rssItems = self.qbtClient.rssItems()

        if operation == "add":
            # Change savePath in order to accept different paths
            if bool(rssRules[name]) == False:
                if category == "Movies":
                    mustContain = name + " 1080p"
                    affectedFeed = rssItems["Movies"]['url']
                    savePath = "/downloads/Movies/" + name
                elif category == "TV Episode":
                    mustContain = name + " S??E?? 1080p"
                    affectedFeed = rssItems["TV"]['url']
                    savePath = "/downloads/Shows" + name
                
                settings = {"enabled": True, "mustContain": mustContain, "mustNotContain": "", "useRegex": False, "episodeFilter": "",
                            "smartFilter": True, "previouslyMatchedEpisodes": [], "affectedFeeds": [affectedFeed], "ignoreDays": 0,
                            "lastMatch": "", "addPaused": True, "assignedCategory": category, "savePath": savePath}    
                
                self.qbtClient.rss_set_rule(rule_name=name, rule_def=settings)
                actionResult = {"response": "added"}
        elif operation == "remove":
            actionResult = {"response": "notFound"}
            for rule in rssRules:
                if rule.title() == name:
                    self.qbtClient.rss_remove_rule(rule_name=rule)
                    actionResult = {"response": "removed"}
        elif operation == "search":
            if bool(rssRules[name]) == True:
                actionResult = {"response": "found"}
            elif bool(rssRules[name]) == False:
                actionResult = {"response": "notFound"}
            
        return actionResult
# ==================================================================================================
    def moviesHandler(self, torrent):
        # Integrate scanner work here after
        # It may be more code, but its easier to debug
        pass
# ==================================================================================================
    def tvHandler(self, torrent):
        # Integrate scanner work here after
        # It may be more code, but its easier to debug
        pass
# ==================================================================================================
    def __init__(self, data, plmPath):
        self.loggerData = data['logger']
        self.username = data['username']
        self.password = data['password']
        self.port = data['port']
        self.mediaExt = data['mediaExt']

        self.movieRegex = ["\.\d{4}\.", "\ \d{4}\ ", "\(\d{4}\)"]
        self.tvRegex = ["\.s\d{2}e\d{2}\.", "\ \s\d{2}e\d{2}\ "]

        self.dbRequest = {"status": "empty", "operation": None, "category": None, "data": {}, "result": {}}
        self.fileRequest = {"status": "empty", "operation": None, "category": None, "data": {}, "result": {}}
        self.rarbgRequest = {"status": "empty", "operation": None, "category": None, "data": {}, "result": {}}
        self.tmdbRequest = {"status": "empty", "operation": None, "category": None, "data": {}, "result": {}}

        self.qbtLogger = loggerSetup(plmPath, self.loggerData)
        self.qbtLogger.info(f"New QBTManager instance created")

        try:
            self.qbtClient = qbittorrentapi.Client("localhost", self.port, self.username, self.password)
            self.qbtLogger.info(f"qbtClient successfully created")
            try:
                self.qbtClient.auth_log_in()
                self.qbtLogger.info(f"qbtClient successfully authenticated")
            except:
                self.qbtLogger.warning(f"Error authenticating qbtClient")
        except:
            self.qbtLogger.warning(f"Error creating qbtClient on localhost")

        self.scannerThread = threading.Thread(target=self.torrentScanner, args=())
        try:
            self.scannerThread.start()
            self.qbtLogger.info(f"Thread started: {self.scannerThread.name}")
        except:
            self.qbtLogger.warning(f"Error starting thread: {self.scannerThread.name}")
