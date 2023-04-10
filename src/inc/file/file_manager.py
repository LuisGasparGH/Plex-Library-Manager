import logging, os, time, pathlib, threading

class File_Manager:
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
        self.file_logger = logging.getLogger(logger_name)
        self.file_logger.setLevel(logging.INFO)
        self.file_logger.addHandler(handler)
        
    def __init__(self, data, plm_path):
        self.plm_path = plm_path
        self.logger_data = data['logger']
        self.path = data['path']
        
        self.logger_setup()
        self.file_logger.info(f"New File_Manager instance created")

# for entry in config['entries']:
#     logging.info(f"Now modifying: {entry}")
#     folder_name = entry['folder_name']
#     folder_path = plex_path + folder_name
#     series_id = entry['tmdb_id']
#     continuous_episodes = entry['continuous_episodes']
#     tv_endpoint = tmdb_endpoint + str(series_id) + "?api_key=" + str(tmdb_apikey)
#     tmdb_series_info = requests.get(tv_endpoint).json()
#     logging.info(f"Request made: {tv_endpoint}")
#     series_name = tmdb_series_info['name']

#     if folder_name != series_name:
#         new_path = plex_path + series_name
#         os.rename(folder_path, new_path)
#         logging.warning(f"Folder name change: {folder_path} -> {new_path}")
#         folder_path = new_path

#     has_season_zero = False
#     total_seasons = len(tmdb_series_info['seasons'])
#     present_seasons = len(os.listdir(folder_path))
#     season_difference = total_seasons - present_seasons
#     episode_number = 1
    
#     for season in tmdb_series_info['seasons']:
#         season_number = season['season_number']
        
#         if season_number == 0:
#             has_season_zero = True
#             season_difference -= 1
#             total_seasons -= 1
#             continue
        
#         if season_difference != 0:
#             logging.warning(f"Missing season: {series_name} has {present_seasons} out of {total_seasons} seasons")
#             season_difference = 0
        
#         logging.info(f"Modifying season: {season_number}")
#         season_appendix = 'S' + str(season_number).zfill(2)
#         season_path = folder_path + "/Season " + str(season_number) + "/"
        
#         if os.path.exists(season_path):
#             file_list = sorted(os.listdir(season_path))
            
#             if len(file_list) != season['episode_count'] and tmdb_series_info['in_production'] == False:
#                 has_missing_episodes = True
#                 logging.warning(f"Missing/Extra episode: {series_name} Season {season_number} has {len(file_list)} out of {season['episode_count']} episodes")

#             # TO DO - DETECT DOUBLE EPISODES BASED ON MISSING FILES AND THEN LAUNCH DATE
#             if continuous_episodes == "False":
#                 episode_number = 1
            
#             for episode in file_list:
#                 episode_path = season_path + episode
                
#                 if os.path.isfile(episode_path):
#                     file_name, file_ext = os.path.splitext(episode_path)
#                     episode_appendix = 'E' + str(episode_number).zfill(2)
#                     tv_season_endpoint = tmdb_endpoint + str(series_id) + "/season/" + str(season_number) + "/episode/" + str(episode_number) + "?api_key=" + str(tmdb_apikey)
#                     tmdb_episode_info = requests.get(tv_season_endpoint).json()
#                     logging.info(f"Request made: {tv_season_endpoint}")
#                     episode_title = tmdb_episode_info['name'].replace("/", "-")
#                     new_path = season_path + series_name + " " + season_appendix + episode_appendix + " - " + episode_title + file_ext
                    
#                     if episode_path != new_path:
#                         os.rename(episode_path, new_path)
#                         logging.info(f"Episode name change: {episode_path} -> {new_path}")
                    
#                     episode_number += 1