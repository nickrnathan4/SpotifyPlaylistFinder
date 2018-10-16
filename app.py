import os
import pprint
import time
import re
import os.path
import spotipy
import datetime
import re
import csv
from functools import reduce
from spotipy.oauth2 import SpotifyClientCredentials


#######################################################################################################################
# CONSTANTS
#######################################################################################################################

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

SIMILAR_ARTISTS = [
    'Charlotte Cardin',
    'Charlie Puth',
    'Sinead Harnett',
    'Brandy',
    'Janet Jackson',
    'Mariah Carey',
    'Michael Blume',
    'Jessie J',
    'Anna Wise',
    'Kehlani',
    'Foushee',
    'Ryn Weaver',
    'MO',
    'Deborah Cox',
    'Jazmine Sullivan',
    'Kate Kay Es',
    'Maggie Lindemann',
    'Demi Lovato',
    'Rihanna',
    'JoJo',
    'Lauv',
    'Madison Ryann Ward'
]

KEYWORDS = [
    'fresh',
    'indie',
    'new music',
    'girl',
    'woman',
    'soul',
    'neo-soul',
    'indie girl',
    'indie soul',
    'girl soul',
    'new indie',
    'new soul',
    'new girl',

    'Charlotte Cardin',
    'Charlie Puth',
    'Sinead Harnett',

]

INVALID_OWNER = [
    'spotify',
    'sonymusicentertainment'
]

INVALID_OWNER_REGEX = [
    r'sony',
    r'^spotify.*',
    r'^warner.*',
    r'^universal.*',
    r'^\d.*',
    r'^filtr.*',
    r'^digster.*',
    r'^playlistr.*',
    r'^topsify.*',
    r'^\_.*',
    r'.*official$',
    r'.*music$',
    r'.*spotify$'

]

CATEGORIES = [
    'Top Lists',
    'Pop',
    'Mood',
    'Hip-Hop',
    'Workout',
    'Chill',
    'Electronic/Dance',
    'Focus',
    'Rock',
    'Party',
    'Decades',
    'Country',
    'Sleep',
    'Latin',
    'R&B',
    'Romance',
    'Indie',
    'Jazz',
    'Gaming',
    'Classical',
    'Comedy',
    'Reggae',
    'Travel',
    'Metal',
    'Soul',
    'Dinner',
    'Blues',
    'Funk',
    'Punk',
    'Folk & Americana',
    'WHM',
    'Wrapped',
    'Trending',
    'Kids',
    'K-Pop'
  ]

TARGETED_CATEGORIES = [
    'pop',
    'indie_alt',
    '2017',
]

FOLLOWER_COUNT_THRESHOLD = 100

API_PACING_SECS = -1

EMOJI_PATTERNS = re.compile(
    u"(\ud83d[\ude00-\ude4f])|"  # emoticons
    u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
    u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
    u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
    u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
    "+", flags=re.UNICODE)

#######################################################################################################################
# UTILS
#######################################################################################################################

printer = pprint.PrettyPrinter(indent=2)


def get_timestamp():
    ts = datetime.datetime.now()
    return '' + str(ts.hour) + str(ts.minute) + str(ts.second) + str(ts.microsecond)


def strip_emojis(v):
    if type(v) is unicode:
        return EMOJI_PATTERNS.sub(r'', v)
    else:
        return v.__str__()


def convert_to_utf8(dict_list):
    result = []
    for d in dict_list:
        result.append({k: strip_emojis(v).encode('utf8') for k, v in d.items()})
    return result


#######################################################################################################################
# POPULATION DETERMINATION
#######################################################################################################################

def out_to_csv(fout, dict_list):
    if dict_list:
        utf8_dict_list = convert_to_utf8(dict_list)
        mode = 'w'
        append = os.path.exists(fout)
        if append:
            mode = 'a+'
        with open(fout, mode) as csv_file:
            writer = csv.DictWriter(csv_file, utf8_dict_list[0].keys())
            if not append:
                writer.writeheader()
            writer.writerows(utf8_dict_list)


def is_valid_owner(playlist):
    if 'owner' in playlist.keys():
        owner = playlist['owner']
        # if owner.isdigit():
        #     return False
        if owner in INVALID_OWNER:
            return False
        for rgx in INVALID_OWNER_REGEX:
            regexp = re.compile(rgx)
            if bool(regexp.search(owner)):
                return False
        return True
    return False


def filter_invalid_owners(playlists):
    return list(filter(lambda playlist: is_valid_owner(playlist), playlists))


def search_playlists(client, url, search_term=''):
    playlists = []
    if API_PACING_SECS > 0:
        time.sleep(API_PACING_SECS)
    resp = client._get(url, None, None)
    if resp:
        playlists.extend(list(map(lambda p: {'href': p['href'],
                                             'search_term': search_term,
                                             'owner': p['owner']['id']
                                             },
                                  resp['playlists']['items'])))
    result = {'playlists': playlists}
    if 'next' in resp['playlists'].keys():
        result['next'] = resp['playlists']['next']
    return result


def _fetch_playlists(client, query_set, type='keyword', page_level=1):
    playlists_all = []
    for query in query_set:
        print(query)
        keyword_results = []
        resp = {'playlists': []}
        if type == 'categories':
            resp['next'] = 'https://api.spotify.com/v1/browse/categories/' + query + '/playlists?offset=0&limit=50'
        else:
            resp['next'] = 'https://api.spotify.com/v1/search?query=' + query + '&type=playlist&offset=0&limit=50'
        level = 0
        while level < page_level:
            print('Level: ' + str(level))
            level += 1
            resp = search_playlists(client, resp['next'], query)
            printer.pprint(resp)
            if 'playlists' in resp.keys():
                keyword_results.extend(resp['playlists'])
                if resp['next'] is None:
                    break

        playlists_all.extend(keyword_results)

    unique_playlists = list({playlist['href']: playlist for playlist in playlists_all}.values())
    print("Unique Playlist Count: " + len(unique_playlists).__str__())
    return filter_invalid_owners(unique_playlists)


def fetch_playlists(client, keywords=True, categories=False):
    playlists = []
    if keywords:
        playlists.extend(_fetch_playlists(client, query_set=KEYWORDS, type='keyword', page_level=21))
    if categories:
        playlists.extend(_fetch_playlists(client, query_set=TARGETED_CATEGORIES, type='categories', page_level=21))
    print("Valid Playlist Count: " + len(playlists).__str__())
    out_to_csv('output/playlist_hrefs_' + get_timestamp() + '.txt', playlists)


#######################################################################################################################
# FULL PLAYLIST COLLECTION
#######################################################################################################################

def fetch_playlist_full(client, url):
    try:
        valid = True
        resp = client._get(url, None, None)
    except Exception:
        print("GET ERROR: " + resp.__str__())
        valid = False

    return resp, valid


def parse_artists(playlist):
    artists = []
    tracks = playlist['tracks']['items']
    if tracks:
        for track in tracks:
            artists.append(list(map(lambda x: x['name'], track['track']['artists'])))
        return list(set(reduce((lambda x, y: x + y), artists)))
    return []


def parse_playlist_full(playlist):
    result = {}
    result['playlist_name'] = playlist['name']
    result['owner_id'] = playlist['owner']['id']
    result['owner_type'] = playlist['owner']['type']
    result['followers'] = playlist['followers']['total']
    result['artists'] = parse_artists(playlist)
    result['artist_matches'] = []
    return result


def contains_similar_artists(playlist, similar_artists):
    return not set(playlist['artists']).isdisjoint(similar_artists)


def get_artist_matches(artists, similar_artists):
    return list(set(artists) & set(similar_artists))


def parse_line(line_in):
    vals = line_in.rstrip().split(',')
    return {'href': vals[2], 'search_term': vals[1]}


def read_hrefs(fin):
    with open(fin) as f:
        content = f.readlines()[1:]
        return [parse_line(x) for x in content]


def is_valid_follower_count(playlist):
    if playlist['followers'] < FOLLOWER_COUNT_THRESHOLD:
        return False
    return True


def is_valid(playlist):
    if playlist['owner_id'].isdigit():
        return False
    if playlist['owner_id'] in INVALID_OWNER:
        return False
    if playlist['followers'] < FOLLOWER_COUNT_THRESHOLD:
        return False
    for rgx in INVALID_OWNER_REGEX:
        regexp = re.compile(rgx)
        if bool(regexp.search(playlist['owner_id'])):
            return False
    return True


def filter_results(dict_list):
    # return list(filter(lambda playlist: is_valid(playlist), dict_list))
    return list(filter(lambda playlist: is_valid_follower_count(playlist), dict_list))


#######################################################################################################################
# CATEGORIES
#######################################################################################################################

def fetch_categories(client, url, attr='id'):
    resp = client._get(url, None, None)
    categories = []
    if resp:
        items = resp['categories']['items']
        for item in items:
            categories.append(item[attr])
    result = {'categories': categories}
    if 'next' in resp['categories'].keys():
        result['next'] = resp['categories']['next']
    return result


def fetch_categories_all(client):
    categories_all = []
    resp = {'next': 'https://api.spotify.com/v1/browse/categories', 'categories': []}
    while True:
        resp = fetch_categories(client, resp['next'])
        print(resp)
        if 'categories' in resp.keys():
            categories_all.extend(resp['categories'])
            if resp['next'] is None:
                break
    return categories_all


#######################################################################################################################
# MAIN
#######################################################################################################################

client_credentials_manager = SpotifyClientCredentials(CLIENT_ID, CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# fetch_playlists(sp, keywords=True, categories=True)

# printer.pprint(fetch_categories_all(sp))

# playlists = sp._get('https://api.spotify.com/v1/browse/categories/indie_alt/playlists?offset=20&limit=20', None, None)
# printer.pprint(playlists)

# hrefs = read_hrefs("output/playlist_hrefs_144936248352.txt")
# ts = get_timestamp()
# results = []
# size = len(hrefs)
# current = 0
# for href in hrefs:
#     current += 1
#     print(str(current) + ' of ' + str(size))
#     playlist = fetch_playlist_full(sp, href['href'])
#     result = parse_playlist_full(playlist)
#     if contains_similar_artists(result, SIMILAR_ARTISTS):
#         result['artist_matches'] = get_artist_matches(result['artists'], SIMILAR_ARTISTS)
#         result['search_term'] = href['search_term']
#         del result['artists']
#         results.append(result)
#
# out_to_csv('output/final_' + ts + '.csv', filter_results(results))
#
