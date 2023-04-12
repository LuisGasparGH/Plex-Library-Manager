import time
#  
#   Requests format:
#      request = {
#          "status": "empty" || "new" || "processing" || "complete"
#          "operation": "add" || "remove" || "modify" || "search"
#          "category": "Movies || "TV" || "TV Season" || "TV Episode"
#          "data":{"field1": ..., "field2":..., ...}
#          "result": {"response": ..., "field1": ..., "field2": ..., ...}
#      }
#
# ==================================================================================================
def sendDBRequest(self, requestPayload):
    self.dbRequest['operation'] = requestPayload['operation']
    self.dbRequest['category'] = requestPayload['category']
    self.dbRequest['data'] = requestPayload['data']
    self.dbRequest['status'] = "new"

    while self.dbRequest['status'] != "complete":
        time.sleep(0.5)

    self.dbRequest['status'] = "empty"
    self.dbRequest['operation'] = None
    self.dbRequest['category'] = None
    self.dbRequest['data'] = {}
# ==================================================================================================
def sendFileRequest(self, requestPayload):
    self.fileRequest['operation'] = requestPayload['operation']
    self.fileRequest['category'] = requestPayload['category']
    self.fileRequest['data'] = requestPayload['data']
    self.fileRequest['status'] = "new"

    while self.fileRequest['status'] != "complete":
        time.sleep(0.5)

    self.fileRequest['status'] = "empty"
    self.fileRequest['operation'] = None
    self.fileRequest['category'] = None
    self.fileRequest['data'] = {}
# ==================================================================================================
def sendPlexRequest(self, requestPayload):
    self.plexRequest['operation'] = requestPayload['operation']
    self.plexRequest['category'] = requestPayload['category']
    self.plexRequest['data'] = requestPayload['data']
    self.plexRequest['status'] = "new"

    while self.plexRequest['status'] != "complete":
        time.sleep(0.5)

    self.plexRequest['status'] = "empty"
    self.plexRequest['operation'] = None
    self.plexRequest['category'] = None
    self.plexRequest['data'] = {}
# ==================================================================================================
def sendQBTRequest(self, requestPayload):
    self.qbtRequest['operation'] = requestPayload['operation']
    self.qbtRequest['category'] = requestPayload['category']
    self.qbtRequest['data'] = requestPayload['data']
    self.qbtRequest['status'] = "new"

    while self.qbtRequest['status'] != "complete":
        time.sleep(0.5)

    self.qbtRequest['status'] = "empty"
    self.qbtRequest['operation'] = None
    self.qbtRequest['category'] = None
    self.qbtRequest['data'] = {}
# ==================================================================================================
def sendTMDBRequest(self, requestPayload):
    self.tmdbRequest['operation'] = requestPayload['operation']
    self.tmdbRequest['category'] = requestPayload['category']
    self.tmdbRequest['data'] = requestPayload['data']
    self.tmdbRequest['status'] = "new"

    while self.tmdbRequest['status'] != "complete":
        time.sleep(0.5)

    self.tmdbRequest['status'] = "empty"
    self.tmdbRequest['operation'] = None
    self.tmdbRequest['category'] = None
    self.tmdbRequest['data'] = {}
# ==================================================================================================