import pymongo
import nullmongo
from copy import copy
from time import time

class Statistics(object):

    def __init__(self, dbUri, dbName=''):
        try:
            client = pymongo.MongoClient(dbUri)
            if dbName == '':
                dbName = pymongo.uri_parser.parse_uri(dbUri)['database']
            db = client[dbName]
            self.stats_profiles = db.stats_profiles
            self.stats_games_for_profiles = db.stats_games_for_profiles
            self.stats_games = db.stats_games
        except Exception, err:
            print "WARNING: Statistics is using null storage"
            print "  Exception: %s" % err
            self.stats_profiles = nullmongo.NullCollection()
            self.stats_games_for_profiles = nullmongo.NullCollection()
            self.stats_games = nullmongo.NullCollection()


    def putUser(self, user):
        u = copy(user)
        u['timestamp'] = time()
        self.stats_profiles.insert(u)


    def putGamesForUser(self, userId, games):
        self.stats_games_for_profiles.insert({ 'userId': userId, 'timestamp': time(), 'games': games })


    def detailsFetched(self, gameId):
        self.stats_games.insert({ 'gameId': gameId, 'timestamp': time() })

