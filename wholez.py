import os
import pprint
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import app


#######################################################################################################################
# CONFIG
#######################################################################################################################

app.SIMILAR_ARTISTS = [
    'Alesso',
    'Rain or Shine',
    'Dillon Francis',
    'Kygo',
    'James Hersey',
    'Elohim',
    'Whethan',
    'Keiynan Lonsdale',
    'Eden Prince',
    'DJ Snake',
    'Bipolar Sunshine',
    'Lauv',
    'Cheat Codes',
    'CVBZ',
    'Cash Cash',
    'Soulive'
]

app.KEYWORDS = [
    'lush+techno',
    'new+music',
    'tropical',
    'vibe',
    'electronic',
    'lovestep',
    'new+mellow',
    'dance+techno',
    'summer+house',
    'party+techno',
    'lush+edm',
    'vibe+edm',
    'new+edm',
    'tropical+edm'
]

app.TARGETED_CATEGORIES = [
    'edm_dance',
    'chill'
]

app.FOLLOWER_COUNT_THRESHOLD = 300
app.API_PACING_SECS = 1

#######################################################################################################################
# MAIN
#######################################################################################################################

client_credentials_manager = SpotifyClientCredentials(app.CLIENT_ID, app.CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# app.fetch_categories_all(sp)
#
# app.fetch_playlists(sp, keywords=True, categories=True)

# playlists = sp._get('https://api.spotify.com/v1/browse/categories/edm_dance/playlists?offset=0&limit=50', None, None)
# app.printer.pprint(playlists)

hrefs = app.read_hrefs("output/playlist_hrefs_234613981008.txt")
ts = app.get_timestamp()
outfile = 'output/final_' + ts + '.csv'
size = len(hrefs)
current = 0
for href in hrefs:
    try:
        current += 1
        print(str(current) + ' of ' + str(size))
        playlist, valid = app.fetch_playlist_full(sp, href['href'])
        if not valid:
            continue
        result = app.parse_playlist_full(playlist)
        if app.contains_similar_artists(result, app.SIMILAR_ARTISTS):
            result['artist_matches'] = app.get_artist_matches(result['artists'], app.SIMILAR_ARTISTS)
            result['search_term'] = href['search_term']
            del result['artists']
            results = app.filter_results([result])
            if results:
                print("Writing to file")
                app.out_to_csv(outfile, results)
    except Exception:
        print("ERROR: some exception occurred for href: " + href.__str__())




