import logging, os, time, pathlib, threading, re
import qbittorrentapi

from inc.logger.logger_setup import logger_setup

class QBT_Manager:
# ==================================================================================================
    def scanner(self):
        self.qbt_logger.info(f"Thread active: {self.qbt_scanner_thread.name}")
        
        while True:
            self.paused = self.qbt_client.torrents_info(status_filter="paused")
            self.seeding = self.qbt_client.torrents_info(status_filter="seeding")
            
            if len(self.paused) != 0:
                self.qbt_logger.info(f"Paused torrents found: {len(self.paused)}")
                
                for torrent in self.paused:
                    if torrent.category == "Movies":
                        self.movies_handler(torrent=torrent, status="paused")
                    elif torrent.category == "TV Episode" or torrent.category == "TV Season":
                        self.tv_handler(torrent=torrent, status="paused")
                    else:
                        self.qbt_logger.warning(f"Incompatible category detected: {torrent.category}, on torrent {torrent.name}, please review manually")
            
            if len(self.seeding) != 0:
                self.qbt_logger.info(f"Seeding torrents found: {len(self.seeding)}")
                for torrent in self.seeding:
                    if torrent.category == "Movies":
                        self.movies_handler(torrent=torrent, status="seeding")
                    elif torrent.category == "TV Episode" or torrent.category == "TV Season":
                        self.tv_handler(torrent=torrent, status="seeding")
            
            time.sleep(3600)
# ==================================================================================================
    # TO DO - Add protection against different torrent name patterns (test from various websites to catch new patterns)
    def movies_handler(self, torrent, status):
        if status == "paused":
            self.qbt_logger.info(f"Handling paused {torrent.category} torrent: {torrent.name}")

            movie_name = torrent.name.split(" (")[0]
            self.qbt_logger.info(f"Details gathered from {torrent.category} torrent: title: {movie_name}")
            torrent_files = self.qbt_client.torrents_files(torrent_hash=torrent.hash)
            
            for file in torrent_files:
                file_extension = pathlib.Path(file.name).suffix

                if file_extension not in self.supported_extensions:
                    try:
                        self.qbt_client.torrents_file_priority(torrent_hash=torrent.hash, file_ids=file.id, priority=0)
                        self.qbt_logger.info(f"Non-media file removed from {torrent.name}: {file.name}")
                    except:
                        self.qbt_logger.warning(f"Error removing non-media file from {torrent.name}: {file.name}")
                elif file_extension in self.supported_extensions:
                    new_name = movie_name + file_extension
                    try:
                        self.qbt_client.torrents_rename_file(torrent_hash=torrent.hash, old_path=file.name, new_path=new_name)
                        self.qbt_logger.info(f"Media file renamed in {torrent.name}: {file.name} -> {new_name}")
                    except:
                        self.qbt_logger.warning(f"Error renaming media file in {torrent.name}: {file.name}")
            
            new_save_path = torrent.save_path + "/" + movie_name
            try:
                self.qbt_client.torrents_set_save_path(save_path=new_save_path, torrent_hashes=torrent.hash)
                self.qbt_logger.info(f"Save path changed in {torrent.name}: {torrent.save_path} -> {new_save_path}")
            except:
                self.qbt_logger.warning(f"Error changing save path: {torrent.name}")

            try:
                self.qbt_client.torrents_rename(torrent_hash=torrent.hash, new_torrent_name=movie_name)
                self.qbt_logger.info(f"Torrent renamed: {torrent.name} -> {movie_name}")
            except:
                self.qbt_logger.warning(f"Error renaming torrent: {torrent.name}")
            
            try:
                self.qbt_client.torrents_resume(torrent_hashes=torrent.hash)
                self.qbt_logger.info(f"Torrent resumed: {movie_name}")
            except:
                self.qbt_logger.warning(f"Error resuming torrent: {torrent.name}")
        elif status == "seeding":
            self.qbt_logger.info(f"Handling seeding {torrent.category} torrent: {torrent.name}")
            self.db_manager_update_entry = {"status": "new", "name": torrent.name, "category": "Movies", "save_path": torrent.save_path}
            self.qbt_logger.info(f"New DB update request sent to PLM: {self.db_manager_update_entry}")
            
            while self.db_manager_update_entry['status'] != "completed":
                time.sleep(0.5)
            
            self.qbt_logger.info(f"Request successfully completed")
            self.db_manager_update_entry['status'] = "empty"
            
            try:
                self.qbt_client.torrents_delete(delete_files=False, torrent_hashes=torrent.hash)
                self.qbt_logger.info(f"Torrent deleted: {torrent.name}")
            except:
                self.qbt_logger.warning(f"Error deleting torrent: {torrent.name}")
# ==================================================================================================
    # TO DO - IN TV EPISODE, ADAPT REGEX TO DETECT DOUBLE EPISODES (SxxExx-xx)
    def tv_handler(self, torrent, status):
        if status == "paused":
            self.qbt_logger.info(f"Handling paused {torrent.category} torrent: {torrent.name}")
            
            if torrent.category == "TV Episode":
                season_episode = re.findall(self.tv_search_pattern, torrent.name, flags=re.IGNORECASE)
                
                if len(season_episode) != 0:
                    self.qbt_logger.info(f"Season-Episode pattern found in torrent: {torrent.name}")
                    show_name = torrent.name.split(season_episode[0])[0]
                    season_episode = season_episode[0].title()
                    
                    if "." in show_name:
                        show_name = show_name.replace(".", " ").title()
                        if show_name[-1] == " ":
                            show_name = show_name[:-1]
                    
                    self.qbt_logger.info(f"Details gathered from {torrent.category} torrent: title: {show_name}, season-episode: {season_episode}")
                    torrent_files = self.qbt_client.torrents_files(torrent_hash=torrent.hash)
                    
                    for file in torrent_files:
                        file_extension = pathlib.Path(file.name).suffix()
                        
                        if file_extension not in self.supported_extensions:
                            try:
                                self.qbt_client.torrents_file_priority(torrent_hash=torrent.hash, file_ids=file.id, priority=0)
                                self.qbt_logger.info(f"Non-media file removed from torrent: {file.name}")
                            except:
                                self.qbt_logger.warning(f"Error removing non-media file from {torrent.name}: {file.name}")
                        elif file_extension in self.supported_extensions:
                            new_name = show_name + " " + season_episode + file_extension
                            try:
                                self.qbt_client.torrents_rename_file(torrent_hash=torrent.hash, old_path=file.name, new_path=new_name)
                                self.qbt_logger.info(f"Media file renamed in {torrent.name}: {file.name} -> {new_name}")
                            except:
                                self.qbt_logger.warning(f"Error renaming media file in {torrent.name}: {file.name}")
                    
                    season_number = int(season_episode[1:3])
                    new_save_path = torrent.save_path + "/Season " + str(season_number)
                    try:
                        self.qbt_client.torrents_set_save_path(save_path=new_save_path, torrent_hashes=torrent.hash)
                        self.qbt_logger.info(f"Save path changed in {torrent.name}: {torrent.save_path} -> {new_save_path}")
                    except:
                        self.qbt_logger.warning(f"Error changing save path: {torrent.name}")
                    
                    torrent_rename = show_name + "." + season_episode
                    try:
                        self.qbt_client.torrents_rename(torrent_hash=torrent.hash, new_torrent_name=torrent_rename)
                        self.qbt_logger.info(f"Torrent renamed: {torrent.name} -> {torrent_rename}")
                    except:
                        self.qbt_logger.warning(f"Error renaming torrent: {torrent.name}")

                    try:
                        self.qbt_client.torrents_resume(torrent_hashes=torrent.hash)
                        self.qbt_logger.info(f"Torrent resumed: {torrent_rename}")
                    except:
                        self.qbt_logger.warning(f"Error resuming torrent: {torrent.name}")
                elif len(season_episode) == 0:
                    self.qbt_logger.warning(f"No season-episode pattern found in torrent: {torrent.name}, please review manually")
            elif torrent.category == "TV Season":
                # TO DO
                pass
        elif status == "seeding":
            self.qbt_logger.info(f"Handling seeding {torrent.category} torrent: {torrent.name}")
            
            show_save_path = os.path.split(torrent.save_path)[0]
            split_name = torrent.name.split(".")
            name = split_name[0]
            last_dl = split_name[1]
            
            self.db_manager_update_entry = {"status": "new", "name": name, "category": "TV", "save_path": show_save_path, "last_dl": last_dl}
            self.qbt_logger.info(f"New DB update request sent to PLM: {self.db_manager_update_entry}")
            
            while self.db_manager_update_entry['status'] != "completed":
                time.sleep(0.5)
            
            self.qbt_logger.info(f"Request successfully completed")
            self.db_manager_update_entry['status'] = "empty"

            try:
                self.qbt_client.torrents_delete(delete_files=False, torrent_hashes=torrent.hash)
                self.qbt_logger.info(f"Torrent deleted: {torrent.name}")
            except:
                self.qbt_logger.warning(f"Error deleting torrent: {torrent.name}")
# ==================================================================================================
    def __init__(self, data, plm_path):
        self.logger_data = data['logger']
        self.username = data['username']
        self.password = data['password']
        self.port = data['port']
        self.supported_extensions = data['supported_extensions']

        self.tv_search_pattern = "s\d{2}e\d{2}"
        self.db_manager_update_entry = {"status": "empty"}

        self.qbt_logger = logger_setup(plm_path, self.logger_data)
        self.qbt_logger.info(f"New QBT_Manager instance created")

        try:
            self.qbt_client = qbittorrentapi.Client(host="localhost", port=self.port, username=self.username, password=self.password)
            self.qbt_logger.info(f"QBT_Client successfully created")
            try:
                self.qbt_client.auth_log_in()
                self.qbt_logger.info(f"QBT_Client successfully authenticated")
            except:
                self.qbt_logger.warning(f"Error authenticating QBT_Client")
        except:
            self.qbt_logger.warning(f"Error creating QBT_Client on localhost")

        self.qbt_scanner_thread = threading.Thread(target=self.scanner, args=())
        try:
            self.qbt_scanner_thread.start()
            self.qbt_logger.info(f"Thread started: {self.qbt_scanner_thread.name}")
        except:
            self.qbt_logger.warning(f"Error starting thread: {self.qbt_scanner_thread.name}")
