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
def send_db_request(self, request_payload):
    self.db_request['operation'] = request_payload['operation']
    self.db_request['category'] = request_payload['category']
    self.db_request['data'] = request_payload['data']
    self.db_request['status'] = "new"

    while self.db_request['status'] != "complete":
        time.sleep(0.5)

    self.db_request['status'] = "empty"
    self.db_request['operation'] = None
    self.db_request['category'] = None
    self.db_request['data'] = {}
# ==================================================================================================
def send_file_request(self, request_payload):
    self.file_request['operation'] = request_payload['operation']
    self.file_request['category'] = request_payload['category']
    self.file_request['data'] = request_payload['data']
    self.file_request['status'] = "new"

    while self.file_request['status'] != "complete":
        time.sleep(0.5)

    self.file_request['status'] = "empty"
    self.file_request['operation'] = None
    self.file_request['category'] = None
    self.file_request['data'] = {}
# ==================================================================================================
def send_plex_request(self, request_payload):
    self.plex_request['operation'] = request_payload['operation']
    self.plex_request['category'] = request_payload['category']
    self.plex_request['data'] = request_payload['data']
    self.plex_request['status'] = "new"

    while self.plex_request['status'] != "complete":
        time.sleep(0.5)

    self.plex_request['status'] = "empty"
    self.plex_request['operation'] = None
    self.plex_request['category'] = None
    self.plex_request['data'] = {}
# ==================================================================================================
def send_qbt_request(self, request_payload):
    self.qbt_request['operation'] = request_payload['operation']
    self.qbt_request['category'] = request_payload['category']
    self.qbt_request['data'] = request_payload['data']
    self.qbt_request['status'] = "new"

    while self.qbt_request['status'] != "complete":
        time.sleep(0.5)

    self.qbt_request['status'] = "empty"
    self.qbt_request['operation'] = None
    self.qbt_request['category'] = None
    self.qbt_request['data'] = {}
# ==================================================================================================
def send_tmdb_request(self, request_payload):
    self.tmdb_request['operation'] = request_payload['operation']
    self.tmdb_request['category'] = request_payload['category']
    self.tmdb_request['data'] = request_payload['data']
    self.tmdb_request['status'] = "new"

    while self.tmdb_request['status'] != "complete":
        time.sleep(0.5)

    self.tmdb_request['status'] = "empty"
    self.tmdb_request['operation'] = None
    self.tmdb_request['category'] = None
    self.tmdb_request['data'] = {}
# ==================================================================================================