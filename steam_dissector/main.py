from steam_dissector import SteamDissector, GameNotFoundException, UserNotFoundException, SteamUnavailableException
from cache import Cache
import traceback
from statistics import Statistics
from flask import Flask, jsonify
from flask.ext.cors import CORS
import json
from config import Config
import sys, os


config = Config()
# Setup config defaults
config.update({
    # Primary (set by user)
    'mongo_uri': '',
    # Alternative (exported by docker)
    'mongo_port': '',
    # Database name
    'mongo_db': 'steam-dissector',
    #
    'cors_origins': '*',
    'host': '0.0.0.0',
    'port': 8088
})
config.loadFileSection('config.cfg', 'SteamDissector')
config.loadEnv(['HOST', 'PORT', 'MONGO_URI', 'MONGO_PORT', 'MONGO_DB'])

# Stupidly docker env var names
mongoUri = config.get('mongo_uri')
if mongoUri == '':
    mongoUri = config.get('mongo_port', '')
# Stupid mongo not handing tcp://
if isinstance(mongoUri, str):
    mongoUri = mongoUri.replace('tcp://', 'mongodb://')

mongoDb = config.get('mongo_db', '')

corsOrigins = [i for i in config.get('cors_origins', '').split(' ') if i]

print "Config:"
print repr(config)

cache = Cache(dbUri=mongoUri, dbName=mongoDb)
statistics = Statistics(dbUri=mongoUri, dbName=mongoDb)
dissector = SteamDissector(cache, statistics)

app = Flask(__name__)
cors = CORS(app, headers='Content-Type', resources={r'/*': {'origins': corsOrigins}})

def error(msg = '', code = 400, err = True):
    if err:
        app.logger.error(msg)
        trace = traceback.format_exc()
        app.logger.error(trace.replace('%', '%%'))
    return msg, code

def is_vanity_url(profile_id):
    import re
    if re.match("\d{17}", profile_id):
        return False
    return True

@app.route("/")
def default():
  return "use /games/<id> and /profiles/<id> and /profiles/<id>/games"

@app.route("/games/<game_id>")
def get_game(game_id):
    try:
        game = dissector.getDetailsForGame(game_id)
        resp = jsonify(game)
        if 'cache_created' in game:
            resp.headers['X-Cache'] = 'HIT'
            resp.headers['X-CacheCreated'] = game['cache_created']
        else:
            resp.headers['X-Cache'] = 'MISS'
        if 'cache_hits' in game:
            resp.headers['X-CacheHits'] = game['cache_hits']
        return resp
    except GameNotFoundException:
        return error('Game not found', 404)
    except SteamUnavailableException:
        return error('Steam not available', 503)
    except:
        print "Unexpected exception:", sys.exc_info()[1]
        return error('Error while getting game details for id: %s' % game_id)

@app.route("/profiles/<profile_id>")
def get_profile(profile_id):
    vanity_url = is_vanity_url(profile_id)
    try:
        js = dissector.getUser(profile_id, vanity_url)
        js['gamesUrl'] = '/profiles/%s/games' % profile_id
        return jsonify(js)
    except UserNotFoundException:
        return error('Profile not found', 404)
    except SteamUnavailableException:
        return error('Steam not available', 503)
    except:
        print "Unexpected exception:", sys.exc_info()[1]
        return error('Error while getting game details for id: %s' % profile_id)

@app.route("/profiles/<profile_id>/games")
def get_profile_games(profile_id):
    vanity_url = is_vanity_url(profile_id)
    try:
        js = dissector.getGamesForUser(profile_id, vanity_url)
        for game in js:
            game['detailsUrl'] = '/games/%s' % game['id']
        return json.dumps(js)
    except UserNotFoundException:
        return error('Profile not found', 404)
    except SteamUnavailableException:
        return error('Steam not available', 503)
    except:
        print "Unexpected exception:", sys.exc_info()[1]
        return error('Error while getting games for profile id: %s' % profile_id)
