import os, time, pathlib, threading, datetime
import tmdbsimple

from inc.logger.loggerSetup import loggerSetup
from inc.requests.requestsBus import *

class TMDBManager:
# ==================================================================================================
    def listScanner(self):
        self.tmdbLogger.info(f"Thread active: {self.scannerThread.name}")
        self.tvList = self.tmdbClient.Lists(id=self.lists['tv']).info()
        self.movieList = self.tmdbClient.Lists(id=self.lists['movies']).info()

        while True:
            self.tvListItems = self.tvList['items']
            self.movieListItems = self.movieList['items']
            self.tmdbLogger.info(f"Items fetched from lists: Movies (ID {self.lists['movies']}), TV (ID {self.lists['tv']})")

            for movieItem in self.movieListItems:
                self.tmdbLogger.info(f"Sending request: search for entry with ID {movieItem['id']} in database")
                requestPayload = {"operation": "search", "category": "Movies", "data": {"tmdbId": movieItem['id']}}
                sendDBRequest(self, requestPayload)

                self.tmdbLogger.info(f"Search result for database entry with ID {movieItem[id]}: {self.dbRequest['result']['response']}")
                if self.dbRequest['result']['response'] == True:
                    self.tmdbLogger.info(f"Sending request: delete RSS Feed for {movieItem['title']}")
                    requestPayload = {"operation": "remove", "category": "Movies", "data": {"type": "RSS",
                                                                                             "name": movieItem['title'].title()}}
                    sendQBTRequest(self, requestPayload)
                    self.qbtRequest['result'] = {}
                elif self.dbRequest['result']['response'] == False:
                    currentDate = datetime.datetime.today()
                    releaseDate = datetime.datetime.strptime(movieItem['releaseDate'], '%Y-%m-%d')
                    
                    if currentDate < releaseDate:
                        self.tmdbLogger.info(f"Movie not yet released: {movieItem['title']} (release date {movieItem['releaseDate']})")
                        self.tmdbLogger.info(f"Sending request: add RSS Feed for {movieItem['title']}")
                        requestPayload = {"operation": "add", "category": "Movies", "data": {"type": "RSS",
                                                                                              "name": movieItem['title'].title()}}
                        sendQBTRequest(self, requestPayload)
                        self.qbtRequest['result'] = {}
                    elif currentDate > releaseDate:
                        self.tmdbLogger.info(f"Movie already released: {movieItem['title']} (release date {movieItem['releaseDate']})")
                        self.tmdbLogger.info(f"Sending request: try to add Torrent for {movieItem['title']}")
                        requestPayload = {"operation": "add", "category": "Movies", "data": {"type": "Torrent",
                                                                                              "name": movieItem['title'].title()}}
                        sendQBTRequest(self, requestPayload)
                        
                        if self.qbtRequest['result']['response'] == "fail":
                            self.tmdbLogger.info(f"Torrent add failed: no suitable result")
                            self.tmdbLogger.info(f"Sending request: add RSS Feed for {movieItem['title']}")
                            requestPayload = {"operation": "add", "category": "Movies", "data": {"type": "RSS",
                                                                                                  "name": movieItem['title'].title()}}
                            sendQBTRequest(self, requestPayload)
                            self.qbtRequest['result'] = {}
                        elif self.qbtRequest['result']['response'] == "success":
                            self.tmdbLogger.info(f"Torrent add successful: {movieItem['title']}")
                        self.qbtRequest['result'] = {}
                self.dbRequest['result'] = {}

            for tvItem in self.tvListItems:
                self.tmdbLogger.info(f"Sending request: search for entry with ID {tvItem['id']} in database")
                requestPayload = {"operation": "search", "category": "TV", "data": {"tmdbId": tvItem['id']}}
                sendDBRequest(self, requestPayload)

                self.tmdbLogger.info(f"Search result for database entry with ID {tvItem['id']}: {self.dbRequest['result']['response']}")
                if self.dbRequest['result']['response'] == True:
                    self.tmdbLogger.info(f"Fetching details from TMDB: ID {tvItem['id']}")
                    tvDetails = self.detailsItem(category="TV", id=tvItem['id'])
                    
                    productionStatus = tvDetails['in_production']
                    lastAirDate = datetime.datetime.strptime(tvDetails['lastAirDate'], '%Y-%m-%d')
                    weekDelta = datetime.timedelta(days=7)
                    currentDate = datetime.datetime.today()

                    self.tmdbLogger.info(f"TV Show in production: {tvItem['name']} -> {productionStatus}")
                    if productionStatus == False and currentDate > lastAirDate+weekDelta:
                        self.tmdbLogger.info(f"TV Show last episode aired: over 1 week ago ({tvItem['name']} -> {tvDetails['lastAirDate']})")
                        self.tmdbLogger.info(f"Sending request: delete RSS Feed for {tvItem['name']}")
                        requestPayload = {"operation": "remove", "category": "TV", "data": {"type": "RSS", "name": tvItem['name'].title()}}
                        sendQBTRequest(self, requestPayload)
                        self.qbtRequest['result'] = {}
                    elif productionStatus == True or currentDate < lastAirDate+weekDelta:
                        self.tmdbLogger.info(f"TV Show last episode aired: under 1 week ago: {tvItem['name']} -> {tvDetails['lastAirDate']}")
                        self.tmdbLogger.info(f"Sending request: add RSS Feed for episodes of {tvItem['name']}")
                        requestPayload = {"operation": "add", "category": "TV Episode", "data": {"type": "RSS", "name": tvItem['name'].title()}}
                        sendQBTRequest(self, requestPayload)
                        self.qbtRequest['result'] = {}
                elif self.dbRequest['result']['response'] == False:
                    currentDate = datetime.datetime.today()
                    firstAirDate = datetime.datetime.strptime(tvItem['firstAirDate'], '%Y-%m-%d')

                    if currentDate < firstAirDate:
                        self.tmdbLogger.info(f"TV Show not yet on air: {tvItem['name']} (first air date {tvItem['firstAirDate']})")
                        self.tmdbLogger.info(f"Sending request: add RSS Feed for episodes of {tvItem['name']}")
                        requestPayload = {"operation": "add", "category": "TV Episode", "data": {"type": "RSS", "name": tvItem['name'].title()}}
                        sendQBTRequest(self, requestPayload)
                        self.qbtRequest['result'] = {}
                    elif currentDate > firstAirDate:
                        self.tmdbLogger.info(f"TV Show already on air: {tvItem['name']} (first air date {tvItem['firstAirDate']})")
                        self.tmdbLogger.info(f"Sending request: try to add Torrent for first episode of {tvItem['name']}")
                        requestPayload = {"operation": "add", "category": "TV Episode", "data": {"type": "Torrent",
                                                                                                  "name": tvItem['name'].title()}}
                        sendQBTRequest(self, requestPayload)

                        if self.qbtRequest['result']['response'] == "fail":
                            self.tmdbLogger.info(f"Torrent add failed: no suitable result")
                            self.tmdbLogger.info(f"Sending request: add RSS Feed for episodes of {tvItem['name']}")
                            requestPayload = {"operation": "add", "category": "TV Episode", "data": {"type": "RSS",
                                                                                                      "name": tvItem['name'].title()}}
                            sendQBTRequest(self, requestPayload)
                            self.qbtRequest['result'] = {}
                        elif self.qbtRequest['result']['response'] == "success":
                            self.tmdbLogger.info(f"Torrent add successfull: {tvItem['name']}")
                        self.qbtRequest['result'] = {}
                    self.dbRequest['result'] = {}
# ==================================================================================================
    def searchItem(self, category, query):
        self.tmdbLogger.info(f"New TMDB {category} search order received: '{query}'")
        if category == "Movies":
            try:
                searchResult = self.tmdbClient.Search().movie(query=query)
                self.tmdbLogger.info(f"{category} search order successful, sending results back to PLM")
            except:
                self.tmdbLogger.warning(f"Error executing {category} search order: '{query}'")
        elif category == "TV":
            try:
                searchResult = self.tmdbClient.Search().tv(query=query)
                self.tmdbLogger.info(f"{category} search order successful, sending results back to PLM")
            except:
                self.tmdbLogger.warning(f"Error executing {category} search order: '{query}'")
        return searchResult
# ==================================================================================================
    def detailsItem(self, category, id):
        self.tmdbLogger.info(f"New TMDB {category} details order received: ID {id}")
        if category == "Movies":
            try:
                details = self.tmdbClient.Movies(id=id).info()
                self.tmdbLogger.info(f"{category} details order successful, sending results back to PLM")
            except:
                self.tmdbLogger.warning(f"Error executing {category} details order: ID {id}")
        elif category == "TV":
            try:
                details = self.tmdbClient.TV(id=id).info()
                self.tmdbLogger.info(f"{category} details order sucessful, sending results back to PLM")
            except:
                self.tmdbLogger.warning(f"Error executing {category} details order: ID {id}")
        return details
# ==================================================================================================
    def __init__(self, data, plmPath):
        self.loggerData = data['logger']
        self.apiKey = data['apiKey']
        self.lists = data['lists']

        self.dbRequest = {"status": "empty", "operation": None, "category": None, "data": {}, "result": {}}
        self.qbtRequest = {"status": "empty", "operation": None, "category": None, "data": {}, "result": {}}

        self.tmdbLogger = loggerSetup(plmPath, self.loggerData)
        self.tmdbLogger.info(f"New TMDBManager instance created")

        try:
            self.tmdbClient = tmdbsimple
            self.tmdbClient.apiKey = self.apiKey
            self.tmdbLogger.info(f"tmdbClient successfully created")
        except:
            self.tmdbLogger.warning(f"Error creating tmdbClient")

        self.scannerThread = threading.Thread(target=self.listScanner, args=())
        try:
            self.scannerThread.start()
            self.tmdbLogger.info(f"Thread started: {self.scannerThread.name}")
        except:
            self.tmdbLogger.warning(f"Error starting thread: {self.scannerThread.name}")
