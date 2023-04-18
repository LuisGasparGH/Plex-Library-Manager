import time, pathlib
import pymongo

from inc.logger.loggerSetup import loggerSetup

class DBManager:
    # Database format
    #   Movies: {name, id, savePath, updated}
    #   TV: {name, id, seasonEpisode, savePath, updated}
    #
# ==================================================================================================
    def searchEntry(self, category, query):
        # searchResult: None if nothing is found, object if one is found
        if category == "Movies":
            searchResult = self.moviesCollection.find_one(query)
        elif category == "TV":
            searchResult = self.tvCollection.find_one(query)

        if searchResult != None:
            actionResult = {"result": "found"}
        elif searchResult == None:
            actionResult = {"result": "notFound"}
        
        return actionResult
# ==================================================================================================
    # TO DO - Try and combine similar parts of update entry (mainly insert_one section)
    def modifyEntry(self, operation, category, data):
        if operation == "add":
            if category == "Movies":
                query = {"id": data['id']}
                searchResult = self.searchEntry(category, query)

                if searchResult['result'] == "found":
                    actionResult = {"response": "alreadyExists"}
                    pass
                elif searchResult['result'] == "notFound":
                    data['updated'] = False

                    try:
                        self.moviesCollection.insert_one(data)
                        self.dbLogger.info(f"New Movie document inserted into {self.db.name}: {data}")
                    except:
                        self.dbLogger.warning(f"Error inserting Movies document into {self.db.name}: {data}")

                    actionResult = {"response": "added"}
            elif category == "TV":
                query = {"id": data['id'], "seasonEpisode": data['seasonEpisode']}
                searchResult = self.searchEntry(category, query)

                if searchResult['result'] == "found":
                    actionResult = {"response": "alreadyExists"}
                    pass
                elif searchResult['result'] == "notFound":
                    data['updated'] = False

                    try:
                        self.tvCollection.insert_one(data)
                        self.dbLogger.info(f"New TV document inserted into {self.db.name}: {data}")
                    except:
                        self.dbLogger.warning(f"Error inserting TV document into {self.db.name}: {data}")

                    actionResult = {"response": "added"}
        elif operation == "update":
            markUpdated = {"$set": {"updated": True}}
            if category == "Movies":
                try:
                    updateResult = self.moviesCollection.update_one(data, markUpdated)
                    self.dbLogger.info(f"Moves document updated in {self.db.name}: {data}")
                except:
                    self.dbLogger.warning(f"Error updating Movies document in {self.db.name}: {data}")
            elif category == "TV":
                try:
                    updateResult = self.tvCollection.update_one(data, markUpdated)
                    self.dbLogger.info(f"TV document updated in {self.db.name}: {data}")
                except:
                    self.dbLogger.warning(f"Error updating TV document in {self.db.name}: {data}")

                if updateResult.modified_count != 0:
                    actionResult = {"response": "updated"}
                elif updateResult.modified_count == 0:
                    actionResult = {"response": "notFound"}
        elif operation == "remove":
            if category == "Movies":
                try:
                    removeResult = self.moviesCollection.delete_one(data)
                    self.dbLogger.info(f"Movie document removed from {self.db.name}: {data}")
                except:
                    self.dbLogger.warning(f"Error removing Movies document from {self.db.name}: {data}")
                
                if removeResult.deleted_count != 0:
                    actionResult = {"reponse": "removed"}
                elif removeResult.deleted_count == 0:
                    actionResult = {"response": "notFound"}
            elif category == "TV":
                try:
                    removeResult = self.tvCollection.delete_one(data)
                    self.dbLogger.info(f"TV document removed from {self.db.name}: {data}")
                except:
                    self.dbLogger.warning(f"Error removing TV document from {self.db.name}: {data}")

                if removeResult.deleted_count != 0:
                    actionResult = {"response": "removed"}
                elif removeResult.deleted_count == 0:
                    actionResult = {"response": "notFound"}

        return actionResult
# ==================================================================================================
    def __init__(self, data, plmPath):
        self.loggerData = data['logger']
        self.url = data['url']
        self.name = data['name']
        self.collections = data['collections']

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

