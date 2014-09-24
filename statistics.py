import pymongo
from copy import copy
from time import time

class Statistics(object):

    def __init__(self, mongoUri):
        client = pymongo.MongoClient(mongoUri)
        dbName = pymongo.uri_parser.parse_uri(mongoUri)['database']
        db = client[dbName]
        self.stats_profiles = db.stats_profiles
        self.stats_games_for_profiles = db.stats_games_for_profiles
        self.stats_games = db.stats_games


    def putUser(self, user):
        u = copy(user)
        u['timestamp'] = time()
        self.stats_profiles.insert(u)


    def putGamesForUser(self, userId, games):
        self.stats_games_for_profiles.insert({ 'userId': userId, 'timestamp': time(), 'games': games })


    def detailsFetched(self, gameId):
        self.stats_games.insert({ 'gameId': gameId, 'timestamp': time() })
