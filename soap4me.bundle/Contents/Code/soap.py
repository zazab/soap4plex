# -*- coding: utf-8 -*-
"""
module soap provides methods for accessing soap shows
"""

import locutils

API_URL = 'http://soap4.me/api/'
LOGIN_URL = 'http://soap4.me/login/'


def login():
    username = Prefs['username']
    password = Prefs['password']

    if not username or not password:
        Log.Debug("No user or password in settings")
        return MessageContainer(
            "Ошибка",
            "Ведите пароль и логин"
        )
    else:

        try:
            values = {
                'login':    username,
                'password': password,
            }

            obj = JSON.ObjectFromURL(
                LOGIN_URL,
                values,
                encoding='utf-8',
                cacheTime=1
            )
        except Exception as ex:
            Log.Debug("can't log in: {}".format(ex))
            obj = []
            return 3

        if len(obj['token']) > 0:
            Dict['sid'] = obj['sid']
            Dict['token'] = obj['token']

            return None
        else:
            Dict['sessionid'] = ""

            return MessageContainer(
                "Ошибка",
                "Отказано в доступе"
            )


def get_soaps():
    filters = Dict['filters']

    url = API_URL + 'soap/'
    if filters['my']:
        url += 'my/'

    soaps = locutils.get(url)
    soaps = sorted(soaps, key=lambda k: k['title'])

    Log.Debug("got {} soaps".format(len(soaps)))

    return locutils.filter_unwatched_soaps(soaps)


def get_episodes(soap_id):
    url = API_URL + 'episodes/' + soap_id
    episodes = locutils.get(url)

    return locutils.filter_unwatched_episodes(episodes)


def get_episode(soap_id, season_num, episode_num):
    'returns episode by soap_id, season, and episode num'
    episodes = get_episodes(soap_id)
    episodes = locutils.filter_episodes_by_season(episodes, season_num)
    episodes = locutils.filter_episodes_by_quality(episodes)

    for episode in episodes:
        if episode['season'] == season_num and episode['episode'] == episode_num:
            return episode

    return None


def get_season_episodes(soap_id, season):
    episodes = get_episodes(soap_id)

    if Prefs['sorting'] != 'да':
        episodes = reversed(episodes)

    return [x for x in episodes if x['season'] == season]


def get_soaps_letters():
    soaps = get_soaps()

    letters = []
    for item in soaps:
        letter = item['title'][0]
        if letter not in letters:
            letters.append(letter)

    return letters


def mark_watched(eid):
    "marks episode eid watched"

    token = Dict['token']
    params = {
        "what": "mark_watched",
        "eid": eid,
        "token": token,
    }

    data = JSON.ObjectFromURL(
        "http://soap4.me/callback/",
        params,
        headers={
            'x-api-token': token,
            'Cookie': 'PHPSESSID=' + Dict['sid']
        }
    )

    if data["ok"] != 1:
        return MessageContainer(
            "Ошибка",
            "Ведите пароль и логин"
        )

    Log.Debug("episode {} marked watched".format(eid))
    return Redirect('https://soap4.me/assets/blank/blank1.mp4')
