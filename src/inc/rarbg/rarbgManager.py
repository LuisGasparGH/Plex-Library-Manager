import rarbgapi

from inc.logger.loggerSetup import loggerSetup

class RARBGManager:
# ==================================================================================================
    def searchTorrent(self, category, id, query):
        if category == "TV Episode":
            searchCategory = self.categories['tv']
        elif category == "Movies":
            searchCategory = self.categories['movies']

        try:
            searchResults = self.rarbgClient.search(search_themoviedb=id,
                                                    search_string=query,
                                                    sort="seeders", 
                                                    categories=[searchCategory],
                                                    extended_response=True)
            searchResults.sort(key=lambda result: result.size)

            if len(searchResults) != 0:
                reqResponse = {"response": True,
                               "title": searchResults[0].title,
                               "infoPage": searchResults[0].info_page,
                               "magnet": searchResults[0].download}
            elif len(searchResults) == 0:
                reqResponse = {"response": False}    
            
            return reqResponse
        except Exception as error:
            print(error)
# ==================================================================================================
    def __init__(self, data, plmPath):
        self.loggerData = data['logger']
        self.categories = data['categories']

        self.qbtRequest = {}

        self.rarbgLogger = loggerSetup(plmPath, self.loggerData)
        self.rarbgLogger.info(f"New RARBGManager instance created")

        try:
            self.rarbgClient = rarbgapi.RarbgAPI()
            self.rarbgLogger.info(f"rarbgClient successfully created")
        except:
            self.rarbgLogger.warning(f"Error creating rarbgClient")