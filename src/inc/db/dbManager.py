import os, time, pathlib, threading
import pymongo

from inc.logger.loggerSetup import loggerSetup

class DBManager:
# ==================================================================================================
    def searchEntry(self, category, query):
        # SEARCH BY ID, NAME, SAVE PATH
        if category == "Movies":
            searchResult = self.moviesCollection.find_one(query)
        elif category == "TV":
            searchResult = self.tvCollection.find_one(query)
        
        return searchResult
# ==================================================================================================
    # TO DO - Try and combine similar parts of update entry (mainly insert_one section)
    def modifyEntry(self, name, savePath):
        self.dbLogger.info(f"Request to update Movie entry received")
        self.tmdbRequest = {"status": "new", "name": name, "category": "Movies"}
        self.dbLogger.info(f"New TMDB Movie search request sent to PLM: {self.tmdbRequest}")
        
        while self.tmdbRequest['status'] != "completed":
            time.sleep(0.5)
        
        result = self.tmdbRequest
        self.dbLogger.info(f"Request successfully completed with result: {result}")
        
        self.tmdbRequest['status'] = "processing"
        movieDocument = {"name": result['tmdbName'], "tmdbId": result['tmdbId'], "savePath": savePath, "updated": False}
        
        try:
            self.moviesCollection.insert_one(movieDocument)
            self.dbLogger.info(f"New Movie document inserted into {self.db.name}: {movieDocument}")
        except:
            self.dbLogger.warning(f"Error inserting Movie document into {self.db.name}: {movieDocument}")

        self.tmdbRequest = {"status": "empty"}   
# ==================================================================================================
    def update_tv_entry(self, name, savePath, lastDL):
        self.dbLogger.info(f"Request to update TV entry received")
        self.dbLogger.info(f"Searching for TV entry in database with save path: {savePath}")
        entrySearch = self.tvCollection.find_one({"savePath": savePath})

        if entrySearch != None:
            self.dbLogger.info(f"Entry found in {self.db.name}: {entrySearch}")
            
            try:
                self.tvCollection.update_one({"_id": entrySearch['_id']}, {"$set": {"lastDL": lastDL}})
                self.dbLogger.info(f"Updated last download field for entry: {entrySearch['name']}")
            except:
                self.dbLogger.warning(f"Error updating entry in {self.db.name}: {entrySearch}")
        elif entrySearch == None:
            self.dbLogger.info(f"Entry not found in {self.db.name}")
            self.tmdbRequest = {"status": "new", "name": name, "category": "TV"}
            self.dbLogger.info(f"New TMDB TV search request sent to PLM: {self.tmdbRequest}")
            
            while self.tmdbRequest['status'] != "completed":
                time.sleep(0.5)
            
            result = self.tmdbRequest
            self.dbLogger.info(f"Request successfully completed with result: {result}")
            
            self.tmdbRequest['status'] = "processing"
            tvDocument = {"name": result['tmdbName'], "tmdbId": result['tmdbId'], "savePath": savePath, "seasons": result['tmdbSeasons'], "lastDL": lastDL}
            
            try:
                self.moviesCollection.insert_one(tvDocument)
                self.dbLogger.info(f"New TV document inserted into {self.db.name}: {tvDocument}")
            except:
                self.dbLogger.warning(f"Error inserting TV document into {self.db.name}: {tvDocument}")

            self.tmdbRequest = {"status": "empty"}
# ==================================================================================================
    def __init__(self, data, plmPath):
        self.loggerData = data['logger']
        self.url = data['url']
        self.name = data['name']
        self.collections = data['collections']

        self.tmdbRequest = {"status": "empty"}

        self.dbLogger = loggerSetup(plmPath, self.loggerData)
        self.dbLogger.info(f"New DBManager instance created")

        try:
            self.DBClient = pymongo.MongoClient(self.url)
            self.dbLogger.info(f"DBClient successfully created")
        except:
            self.dbLogger.warning(f"Error creating DBClient with URL {self.url}")

        self.db = self.DBClient[self.name]
        self.tvCollection = self.db[self.collections['tv']]
        self.moviesCollection = self.db[self.collections['movies']]
        self.dbLogger.info(f"Database and collections selected")

