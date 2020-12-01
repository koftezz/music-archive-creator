import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import spotipy
import spotipy.util as util
import os
import logging
import logging.handlers
from datetime import date
from googlesearch import search
import eyed3
import os
from difflib import SequenceMatcher


# get track name similarity
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


# retrieve tracks
def show_tracks(results):
    df = pd.DataFrame(columns=['track_artist', 'track_name'])

    for j, item in enumerate(results['items']):
        track = item['track']
        print(
            "   %d %32.32s %s" %
            (j, track['artists'][0]['name'], track['name']))

        df = df.append(
            { 'track_artist': track['artists'][0]['name'], 'track_name':
                track['name'] },
            ignore_index=True)
    return df


# get url from beatport
def getURL(query):
    query = "Beatport " + query
    urls = []
    for url in search(query, tld="com", lang="en", num=1, stop=3, pause=2):
        urls.append(url)
    return urls


# get playlist detail from spotify for specific user and playlist
def get_playlist(user, playlist_name=None):
    df2 = pd.DataFrame()
    token = util.prompt_for_user_token(user)
    if token:
        sp = spotipy.Spotify(auth=token)
        playlists = sp.user_playlists(user)
        for playlist in playlists['items']:
            if playlist['owner']['id'] == user:
                if playlist['name'] == playlist_name:
                    logging.info('Playlist name: {0}'.format(playlist['name']))
                    logging.info('Total tracks: {0}'.
                                 format(playlist['tracks']['total']))
                    results = sp.playlist(playlist['id'],
                                          fields="tracks,next")
                    tracks = results['tracks']
                    while tracks['next']:
                        tracks = sp.next(tracks)
                        df1 = show_tracks(tracks)
                        df2 = pd.concat([df1, df2])
        return df2
    else:
        logging.debug("Can't get token for {0}".format(username))
        return None


# get track details from beatport
def get_song_details(url):
    html_doc = requests.get(url[0])
    if html_doc.ok:
        try:
            soup = BeautifulSoup(html_doc.text, 'html.parser')
            genre = soup.findAll(
                'li', { "class":
                            "interior-track-content-item interior-track-genre" })
            genre = genre[0].a.string
            # get bpm
            bpm = soup.find(
                'li',
                { "class": "interior-track-content-item interior-track-bpm" })
            bpm = float(bpm.text.strip().split("BPM", 1)[1][1:])
            # get key
            key = soup.find(
                'li',
                { "class": "interior-track-content-item interior-track-key" })
            key = key.text.strip().split("Key", 1)[1][1:]
            # get name
            name = soup.find('div', { "class": "interior-title" })
            remixed = name.contents[3].contents[0]
            name = name.contents[1].contents[0]

            return genre, key, name, remixed, bpm
        except Exception as e:
            logging.debug("Invalid link")


if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    # set log level
    logger.setLevel(logging.WARNING)

    path = "C://Users//batuhan.organ//Desktop//Music/spotify-techno/"
    run_date = date.today()
    username = "koftezzz"
    track_list = get_playlist(username, playlist_name="Proper t")

    track_list['genre'] = ""
    track_list['name'] = ""
    track_list['remixed'] = ""
    track_list['key'] = ""
    track_list['bpm'] = ""

    for i in range(len(track_list)):

        track = track_list.iloc[i, 0] + " - " + track_list.iloc[i, 1]
        logging.info('Trying song: {0}'.format(track))
        logging.info('{0} out of {1}'.format(len(track_list)))

        url_list = getURL(query=track)
        result = get_song_details(url_list)
        if result:
            track_list.loc[i, 'genre'] = result[0]
            track_list.loc[i, 'key'] = result[1]
            track_list.loc[i, 'name'] = result[2]
            track_list.loc[i, 'remixed'] = result[3]
            track_list.loc[i, 'bpm'] = result[4]
        else:
            logging.info('{0}'.format(result))
        time.sleep(2)

    track_list.to_csv('./tracks/song-details_' + run_date + '.csv')

    # update downloaded songs details
    mp3_list = []
    for file in os.listdir(path):
        if file.endswith(".mp3"):
            mp3_list.append(file)

    track_list['full_name'] = track_list['artist'] + " - " + track_list[
        'songTitle']
    for i in range(len(mp3_list)):
        audio_path = mp3_list[i]

        track_list['name_similarity'] = track_list['full_name'].apply(lambda x:
                                                                      similar(
                                                                          x,
                                                                          audio_path))
        max_index = track_list['name_similarity'].idxmax()
        max_row = track_list.iloc[[max_index]].reset_index()
        if ~max_row.name.isna()[0]:
            if max_row['name_similarity'][0] > 0.4:
                audiofile = eyed3.load(os.path.join(path, audio_path)).tag
                audiofile.setArtist = max_row.artist[0]
                audiofile.setTitle = max_row.songTitle[0]
                audiofile.genre = max_row.genre[0]
                audiofile.bpm = int(max_row.bpm[0])
                audiofile.save()
            else:
                print(audio_path)
                logging.info("Max similarity for the track {0} tracks is {"
                             "1}".format(audio_path,
                                         max_row.name_similarity))