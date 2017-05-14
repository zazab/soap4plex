# -*- coding: utf-8 -*-
"some util methods"

def get(url):
    """
    performs GET request to soap url, setting corresponding headers
    """
    return JSON.ObjectFromURL(
        url,
        headers={
            'x-api-token': Dict['token'],
            'Cookie': 'PHPSESSID=' + Dict['sid']
        },
        cacheTime=0
    )


def make_title(episode):
    'generates episode title'

    new = ''
    if not episode['watched']:
        new = '* '

    season = 'S{}'.format(episode['season'])
    episode_str = 'E{}'.format(episode['episode'])
    quality = episode['quality'].encode('utf-8')
    translate = episode['translate'].encode('utf-8')
    title = episode['title_en'].encode('utf-8').replace('&#039;', "'")
    return u'{}{}{} | {} | {} | {}'.format(
        new, season, episode_str,
        quality, translate, title,
    )


def filter_unwatched_soaps(soaps):
    'filters watched shows if filter new is set'

    if Dict['filters']['new']:
        soaps = [x for x in soaps if x['unwatched'] is not None]
        Log.Debug('{} filtered soaps'.format(len(soaps)))

    return soaps


def filter_unwatched_episodes(episodes):
    'filters watched episodes if filter new is set'

    if Dict['filters']['new']:
        episodes = [x for x in episodes if x['watched'] is None]

    return episodes


def filter_by_letter(soaps):
    'filters shows by first letter if filter letter is set'

    try:
        letter = Dict['filters']['letter']
    except KeyError:
        return soaps

    return [x for x in soaps if x['title'][0] == letter]


def filter_episodes_by_quality(episodes):
    'filters episodes by quality'

    quality = Prefs["quality"]
    only_hd = False

    if quality == "HD":
        for episode in episodes:
            if episode['quality'] == '720p':
                only_hd = True
                break

    if quality == 'HD' and only_hd:
        return [x for x in episodes if x['quality'] == '720p']

    return [x for x in episodes if x['quality'] == 'SD']


def filter_episodes_by_season(episodes, season_num):
    'filter episodes by season'

    return [x for x in episodes if x['season'] == season_num]
