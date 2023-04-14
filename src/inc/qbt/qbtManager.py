import os, time, pathlib, threading, re, json
import qbittorrentapi

from inc.logger.loggerSetup import loggerSetup

class QBTManager:
# ==================================================================================================
    def torrentScanner(self):
        self.qbtLogger.info(f"Thread active: {self.scannerThread.name}")
        
        while True:
            self.paused = self.qbtClient.torrents_info("paused")
            self.seeding = self.qbtClient.torrents_info("seeding")
            
            if len(self.paused) != 0:
                self.qbtLogger.info(f"Paused torrents found: {len(self.paused)}")
                
                for torrent in self.paused:
                    if torrent.category == "Movies":
                        self.movies_handler(torrent=torrent, status="paused")
                    elif torrent.category == "TV Episode" or torrent.category == "TV Season":
                        self.tv_handler(torrent=torrent, status="paused")
                    else:
                        self.qbtLogger.warning(f"Incompatible category detected: {torrent.category}, on torrent {torrent.name}, \
                                                please review manually")
            
            if len(self.seeding) != 0:
                self.qbtLogger.info(f"Seeding torrents found: {len(self.seeding)}")
                for torrent in self.seeding:
                    if torrent.category == "Movies":
                        self.movies_handler(torrent=torrent, status="seeding")
                    elif torrent.category == "TV Episode" or torrent.category == "TV Season":
                        self.tv_handler(torrent=torrent, status="seeding")
            
            time.sleep(3600)
# ==================================================================================================
    def modifyTorrent(self, operation, category, data):
        if operation == "add":
            opResult = self.qbtClient.torrents_add(url=data['magnet'])

            if opResult == "Ok.":
                self.qbtLogger.info(f"Torrent added successfully: {data}")
                
                actionResult = {"response": "success"}
            elif opResult == "Fails.":
                self.qbtLogger.warning(f"Error adding torrent: {data}")

                actionResult = {"response": "failed"}
                
            return actionResult
        elif operation == "modify":
            pass
        elif operation == "remove":
            pass
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
        elif operation == "modify":
            pass
        elif operation == "remove":
            actionResult = {"response": "none_found"}
            for rule in rssRules:
                if rule.title() == name:
                    self.qbtClient.rss_remove_rule(rule_name=rule)
                    actionResult = {"response": "deleted"}
            
            return actionResult
# ==================================================================================================
    # TO DO - Add protection against different torrent name patterns (test from various websites to catch new patterns)
    def movies_handler(self, torrent, status):
        if status == "paused":
            self.qbtLogger.info(f"Handling paused {torrent.category} torrent: {torrent.name}")

            movie_name = torrent.name.split(" (")[0]
            self.qbtLogger.info(f"Details gathered from {torrent.category} torrent: title: {movie_name}")
            torrent_files = self.qbtClient.torrents_files(torrent_hash=torrent.hash)
            
            for file in torrent_files:
                file_extension = pathlib.Path(file.name).suffix

                if file_extension not in self.supported_extensions:
                    try:
                        self.qbtClient.torrents_file_priority(torrent_hash=torrent.hash, file_ids=file.id, priority=0)
                        self.qbtLogger.info(f"Non-media file removed from {torrent.name}: {file.name}")
                    except:
                        self.qbtLogger.warning(f"Error removing non-media file from {torrent.name}: {file.name}")
                elif file_extension in self.supported_extensions:
                    new_name = movie_name + file_extension
                    try:
                        self.qbtClient.torrents_rename_file(torrent_hash=torrent.hash, old_path=file.name, new_path=new_name)
                        self.qbtLogger.info(f"Media file renamed in {torrent.name}: {file.name} -> {new_name}")
                    except:
                        self.qbtLogger.warning(f"Error renaming media file in {torrent.name}: {file.name}")
            
            new_save_path = torrent.save_path + "/" + movie_name
            try:
                self.qbtClient.torrents_set_save_path(save_path=new_save_path, torrent_hashes=torrent.hash)
                self.qbtLogger.info(f"Save path changed in {torrent.name}: {torrent.save_path} -> {new_save_path}")
            except:
                self.qbtLogger.warning(f"Error changing save path: {torrent.name}")

            try:
                self.qbtClient.torrents_rename(torrent_hash=torrent.hash, new_torrent_name=movie_name)
                self.qbtLogger.info(f"Torrent renamed: {torrent.name} -> {movie_name}")
            except:
                self.qbtLogger.warning(f"Error renaming torrent: {torrent.name}")
            
            try:
                self.qbtClient.torrents_resume(torrent_hashes=torrent.hash)
                self.qbtLogger.info(f"Torrent resumed: {movie_name}")
            except:
                self.qbtLogger.warning(f"Error resuming torrent: {torrent.name}")
        elif status == "seeding":
            self.qbtLogger.info(f"Handling seeding {torrent.category} torrent: {torrent.name}")
            self.dbRequest = {"status": "new", "name": torrent.name, "category": "Movies", "save_path": torrent.save_path}
            self.qbtLogger.info(f"New DB update request sent to PLM: {self.dbRequest}")
            
            while self.dbRequest['status'] != "completed":
                time.sleep(0.5)
            
            self.qbtLogger.info(f"Request successfully completed")
            self.dbRequest['status'] = "empty"
            
            try:
                self.qbtClient.torrents_delete(delete_files=False, torrent_hashes=torrent.hash)
                self.qbtLogger.info(f"Torrent deleted: {torrent.name}")
            except:
                self.qbtLogger.warning(f"Error deleting torrent: {torrent.name}")
# ==================================================================================================
    # TO DO - IN TV EPISODE, ADAPT REGEX TO DETECT DOUBLE EPISODES (SxxExx-xx)
    def tv_handler(self, torrent, status):
        if status == "paused":
            self.qbtLogger.info(f"Handling paused {torrent.category} torrent: {torrent.name}")
            
            if torrent.category == "TV Episode":
                season_episode = re.findall(self.tvRegex, torrent.name, flags=re.IGNORECASE)
                
                if len(season_episode) != 0:
                    self.qbtLogger.info(f"Season-Episode pattern found in torrent: {torrent.name}")
                    show_name = torrent.name.split(season_episode[0])[0]
                    season_episode = season_episode[0].title()
                    
                    if "." in show_name:
                        show_name = show_name.replace(".", " ").title()
                        if show_name[-1] == " ":
                            show_name = show_name[:-1]
                    
                    self.qbtLogger.info(f"Details gathered from {torrent.category} torrent: title: {show_name}, season-episode: {season_episode}")
                    torrent_files = self.qbtClient.torrents_files(torrent_hash=torrent.hash)
                    
                    for file in torrent_files:
                        file_extension = pathlib.Path(file.name).suffix()
                        
                        if file_extension not in self.supported_extensions:
                            try:
                                self.qbtClient.torrents_file_priority(torrent_hash=torrent.hash, file_ids=file.id, priority=0)
                                self.qbtLogger.info(f"Non-media file removed from torrent: {file.name}")
                            except:
                                self.qbtLogger.warning(f"Error removing non-media file from {torrent.name}: {file.name}")
                        elif file_extension in self.supported_extensions:
                            new_name = show_name + " " + season_episode + file_extension
                            try:
                                self.qbtClient.torrents_rename_file(torrent_hash=torrent.hash, old_path=file.name, new_path=new_name)
                                self.qbtLogger.info(f"Media file renamed in {torrent.name}: {file.name} -> {new_name}")
                            except:
                                self.qbtLogger.warning(f"Error renaming media file in {torrent.name}: {file.name}")
                    
                    season_number = int(season_episode[1:3])
                    new_save_path = torrent.save_path + "/Season " + str(season_number)
                    try:
                        self.qbtClient.torrents_set_save_path(save_path=new_save_path, torrent_hashes=torrent.hash)
                        self.qbtLogger.info(f"Save path changed in {torrent.name}: {torrent.save_path} -> {new_save_path}")
                    except:
                        self.qbtLogger.warning(f"Error changing save path: {torrent.name}")
                    
                    torrent_rename = show_name + "." + season_episode
                    try:
                        self.qbtClient.torrents_rename(torrent_hash=torrent.hash, new_torrent_name=torrent_rename)
                        self.qbtLogger.info(f"Torrent renamed: {torrent.name} -> {torrent_rename}")
                    except:
                        self.qbtLogger.warning(f"Error renaming torrent: {torrent.name}")

                    try:
                        self.qbtClient.torrents_resume(torrent_hashes=torrent.hash)
                        self.qbtLogger.info(f"Torrent resumed: {torrent_rename}")
                    except:
                        self.qbtLogger.warning(f"Error resuming torrent: {torrent.name}")
                elif len(season_episode) == 0:
                    self.qbtLogger.warning(f"No season-episode pattern found in torrent: {torrent.name}, please review manually")
            elif torrent.category == "TV Season":
                # TO DO
                pass
        elif status == "seeding":
            self.qbtLogger.info(f"Handling seeding {torrent.category} torrent: {torrent.name}")
            
            show_save_path = os.path.split(torrent.save_path)[0]
            split_name = torrent.name.split(".")
            name = split_name[0]
            last_dl = split_name[1]
            
            self.dbRequest = {"status": "new", "name": name, "category": "TV", "save_path": show_save_path, "last_dl": last_dl}
            self.qbtLogger.info(f"New DB update request sent to PLM: {self.dbRequest}")
            
            while self.dbRequest['status'] != "completed":
                time.sleep(0.5)
            
            self.qbtLogger.info(f"Request successfully completed")
            self.dbRequest['status'] = "empty"

            try:
                self.qbtClient.torrents_delete(delete_files=False, torrent_hashes=torrent.hash)
                self.qbtLogger.info(f"Torrent deleted: {torrent.name}")
            except:
                self.qbtLogger.warning(f"Error deleting torrent: {torrent.name}")
# ==================================================================================================
    def __init__(self, data, plmPath):
        self.loggerData = data['logger']
        self.username = data['username']
        self.password = data['password']
        self.port = data['port']
        self.mediaExt = data['mediaExt']

        self.tvRegex = "s\d{2}e\d{2}"
        self.dbRequest = {"status": "empty"}

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
