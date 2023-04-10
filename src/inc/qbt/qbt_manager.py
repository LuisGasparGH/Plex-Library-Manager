import logging, os, time, pathlib, threading, re
import qbittorrentapi

class QBT_Manager:
# ==================================================================================================
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
        self.qbt_logger = logging.getLogger(logger_name)
        self.qbt_logger.setLevel(logging.INFO)
        self.qbt_logger.addHandler(handler)
# ==================================================================================================
    def scanner(self):
        self.qbt_logger.info(f"Thread active: scanner")
        while True:
            self.paused = self.qbt_client.torrents_info(status_filter="paused")
            self.seeding = self.qbt_client.torrents_info(status_filter="seeding")
            if len(self.paused) != 0:
                self.qbt_logger.info(f"{len(self.paused)} paused torrents found")
                for torrent in self.paused:
                    if torrent.category == "Movies":
                        self.movies_handler(torrent=torrent, status="paused")
                    elif torrent.category == "TV Episode" or torrent.category == "TV Season":
                        self.tv_handler(torrent=torrent, status="paused")
                    else:
                        self.qbt_logger.warning(f"Incompatible category detected: {torrent.category}, on torrent {torrent.name}, please review manually")
            if len(self.seeding) != 0:
                self.qbt_logger.info(f"{len(self.seeding)} seeding torrents found")
                for torrent in self.seeding:
                    if torrent.category == "Movies":
                        self.movies_handler(torrent=torrent, status="seeding")
                    elif torrent.category == "TV Episode" or torrent.category == "TV Season":
                        self.tv_handler(torrent=torrent, status="seeding")
            time.sleep(3600)
# ==================================================================================================
    # TO DO - ADD PROTECTION AGAINST DIFFERENT TORRENT NAME PATTERNS (WITHOUT ())
    def movies_handler(self, torrent, status):
        if status == "paused":
            self.qbt_logger.info(f"Handling new {torrent.category} torrent: {torrent.name}")
            movie_name = torrent.name.split(" (")[0]
            self.qbt_logger.info(f"Details gathered from {torrent.category} torrent: title: {movie_name}")
            torrent_files = self.qbt_client.torrents_files(torrent_hash=torrent.hash)
            for file in torrent_files:
                file_extension = pathlib.Path(file.name).suffix
                if file_extension not in self.supported_extensions:
                    self.qbt_client.torrents_file_priority(torrent_hash=torrent.hash, file_ids=file.id, priority=0)
                    self.qbt_logger.info(f"Non-media file removed from torrent: {file.name}")
                elif file_extension in self.supported_extensions:
                    new_name = movie_name + file_extension
                    self.qbt_client.torrents_rename_file(torrent_hash=torrent.hash, old_path=file.name, new_path=new_name)
                    self.qbt_logger.info(f"Media file renamed: {file.name} -> {new_name}")
            new_save_path = torrent.save_path + "/" + movie_name
            self.qbt_client.torrents_set_save_path(save_path=new_save_path, torrent_hashes=torrent.hash)
            self.qbt_logger.info(f"Save path changed: {torrent.save_path} -> {new_save_path}")
            self.qbt_client.torrents_rename(torrent_hash=torrent.hash, new_torrent_name=movie_name)
            self.qbt_logger.info(f"Torrent renamed: {torrent.name} -> {movie_name}")
            self.qbt_client.torrents_resume(torrent_hashes=torrent.hash)
            self.qbt_logger.info(f"Torrent resumed: {movie_name}")
        elif status == "seeding":
            self.qbt_logger.info(f"Handling finished {torrent.category} torrent: {torrent.name}")
            self.db_manager_update_entry = {"status": "new", "name": torrent.name, "category": "Movies", "save_path": torrent.save_path}
            self.qbt_logger.info(f"New DB update request sent to PLM: {self.db_manager_update_entry}")
            while self.db_manager_update_entry['status'] != "completed":
                time.sleep(0.5)
            self.qbt_logger.info(f"Request successfully completed")
            self.db_manager_update_entry['status'] = "empty"
            self.qbt_client.torrents_delete(delete_files=False, torrent_hashes=torrent.hash)
            self.qbt_logger.info(f"Torrent deleted: {torrent.name}")
# ==================================================================================================
    # TO DO - IN TV EPISODE, ADAPT REGEX TO DETECT DOUBLE EPISODES (SxxExx-xx)
    def tv_handler(self, torrent, status):
        if status == "paused":
            self.qbt_logger.info(f"Handling new {torrent.category} torrent: {torrent.name}")
            if torrent.category == "TV Episode":
                season_episode = re.findall(self.tv_search_pattern, torrent.name, flags=re.IGNORECASE)
                if len(season_episode) != 0:
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
                            self.qbt_client.torrents_file_priority(torrent_hash=torrent.hash, file_ids=file.id, priority=0)
                            self.qbt_logger.info(f"Non-media file removed from torrent: {file.name}")
                        elif file_extension in self.supported_extensions:
                            new_name = show_name + " " + season_episode + file_extension
                            self.qbt_client.torrents_rename_file(torrent_hash=torrent.hash, old_path=file.name, new_path=new_name)
                            self.qbt_logger.info(f"Media file renamed: {file.name} -> {new_name}")
                    season_number = int(season_episode[1:3])
                    new_save_path = torrent.save_path + "/Season " + str(season_number)
                    self.qbt_client.torrents_set_save_path(save_path=new_save_path, torrent_hashes=torrent.hash)
                    self.qbt_logger.info(f"Save path changed: {torrent.save_path} -> {new_save_path}")
                    torrent_rename = show_name + "." + season_episode
                    self.qbt_client.torrents_rename(torrent_hash=torrent.hash, new_torrent_name=torrent_rename)
                    self.qbt_logger.info(f"Torrent renamed: {torrent.name} -> {torrent_rename}")
                    self.qbt_client.torrents_resume(torrent_hashes=torrent.hash)
                    self.qbt_logger.info(f"Torrent resumed: {torrent_rename}")
                elif len(season_episode) == 0:
                    self.qbt_logger.warning(f"No season-episode pattern found in torrent: {torrent.name}, please review manually")
            elif torrent.category == "TV Season":
                # TO DO
                pass
        elif status == "seeding":
            self.qbt_logger.info(f"Handling finished {torrent.category} torrent: {torrent.name}")
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
            self.qbt_client.torrents_delete(delete_files=False, torrent_hashes=torrent.hash)
            self.qbt_logger.info(f"Torrent deleted: {torrent.name}")
# ==================================================================================================
    def __init__(self, data, plm_path):
        self.plm_path = plm_path
        self.logger_data = data['logger']
        self.username = data['username']
        self.password = data['password']
        self.port = data['port']
        self.supported_extensions = data['supported_extensions']

        self.tv_search_pattern = "s\d{2}e\d{2}"
        self.db_manager_update_entry = {"status": "empty"}

        self.logger_setup()
        self.qbt_logger.info(f"New QBT_Manager instance created")

        self.qbt_client = qbittorrentapi.Client(host="localhost", port=self.port, username=self.username, password=self.password)
        self.qbt_logger.info(f"Client created")
        self.qbt_client.auth_log_in()
        self.qbt_logger.info(f"Client authenticated")

        self.qbt_scanner_thread = threading.Thread(target=self.scanner, args=())
        self.qbt_scanner_thread.start()
        self.qbt_logger.info(f"Thread started: scanner")
