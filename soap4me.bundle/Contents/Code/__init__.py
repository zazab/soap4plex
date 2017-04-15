# -*- coding: utf-8 -*-
'''
soap4me plex plugin
'''

# created by sergio
# updated by kestl1st@gmail.com (@kestl) v.1.2.3 2016-08-01
# updated by sergio v.1.2.2 2014-08-28

import re
import hashlib
import urllib
import calendar
import time
import json

import locutils
import soap
import plex

VERSION = 2.0
PREFIX = "/video/soap4me"
TITLE = 'soap4.me'
ART = 'art.png'
USER_AGENT = 'xbmc for soap'


def Start():
    'plex plugin init function'

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = TITLE
    DirectoryObject.thumb = R(locutils.ICON)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = USER_AGENT
    HTTP.Headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    HTTP.Headers['Accept-Encoding'] = 'gzip,deflate,sdch'
    HTTP.Headers['Accept-Language'] = 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3'


@handler(PREFIX, TITLE, thumb=locutils.ICON, art=ART)
def main_menu():
    "makes main menu"

    container = ObjectContainer()
    container.add(plex.make_menu_item(
        show_soaps,
        title=u'Все сериалы',
        filters={
            'my': False,
            'new': False
        }
    ))
    container.add(plex.make_menu_item(
        show_soaps,
        title=u'Я смотрю',
        filters={
            "my": True,
            "new": False,
        }
    ))
    container.add(plex.make_menu_item(
        show_soaps,
        title=u'Новые эпизоды',
        filters={
            "my": True,
            "new": True,
        }
    ))

    container.add(PrefsObject(title=u'Настройки', thumb=R('settings.png')))
    return container


@route(PREFIX + '/filters')
def set_filters(title2):
    'shows filter lists'

    # TODO: add some more filters?

    return starts_with_filter(title2)

@route(PREFIX + '/filters/letter')
def starts_with_filter(title2):
    'shows filter by first letter'

    letters = soap.get_soaps_letters()
    container = ObjectContainer(title2=u'Starts With')

    for letter in letters:
        container.add(
            DirectoryObject(
                key=Callback(
                    set_letter_filter,
                    title2=title2,
                    letter=letter,
                ),
                title=letter,
            )
        )

    return container


@route(PREFIX + '/filters/letter/{letter}')
def set_letter_filter(letter, title2):
    "sets letter filter"

    filters = Dict['filters']
    filters['letter'] = letter

    Log.Debug('setting filters: {}'.format(json.dumps(filters, indent=2)))
    Dict['filters'] = filters
    Log.Debug('filters set')

    return show_soaps(title2)


@route(PREFIX + '/soaps', filters={})
def show_soaps(title2, filters=None):
    'show soaps'

    if filters != None:
        Log.Debug("setting filters: {}".format(json.dumps(filters, indent=2)))
        Dict['filters'] = filters

    error = soap.login()
    if error != None:
        return error

    container = ObjectContainer(title2=title2.decode())
    container.add(
        DirectoryObject(
            key=Callback(set_filters, title2=title2),
            title=u'Фильтровать'
        )
    )

    soaps = soap.get_soaps()
    soaps = locutils.filter_by_letter(soaps)

    for item in soaps:

        container.add(plex.make_tvshow_item(show_seasons, item))
    return container


@route(PREFIX + '/soaps/{soap_id}')
def show_seasons(soap_id, soap_title):
    'show tvshow seasons'
    seasons = {}
    season_episodes = {}

    episodes = soap.get_episodes(soap_id)

    for episode in episodes:
        season_num = int(episode['season'])
        episode_num = int(episode['episode'])

        if season_num not in seasons:
            seasons[season_num] = episode['season_id']

        if season_num not in season_episodes:
            season_episodes[season_num] = []

        if episode_num not in season_episodes[season_num]:
            season_episodes[season_num].append(episode_num)

    container = ObjectContainer(title2=soap_title)

    for season in seasons:
        season_id = seasons[season]
        container.add(
            plex.make_season_item(
                show_episodes,
                soap_id, soap_title,
                season, season_id,
                season_episodes,
            )
        )

    return container


@route(PREFIX + '/soaps/{soap_id}/{season_num}')
def show_episodes(soap_id, season_num, soap_title):
    'show season episodes'

    container = ObjectContainer(title2=u'%s - %s сезон ' % (soap_title, season_num))

    episodes = soap.get_season_episodes(soap_id, season_num)
    episodes = locutils.filter_episodes_by_quality(episodes)

    for episode in episodes:
        container.add(plex.make_episode_item(play_episode, episode_url, episode))

    return container


@route(PREFIX + '/soaps/{soap_id}/{season_num}/{episode_num}')
def play_episode(soap_id, season_num, episode_num):
    'starts episode playing or marks episode as watched'

    episode_obj = soap.get_episode(soap_id, season_num, episode_num)
    if episode_obj is None:
        Log.Critical("episode {} not found".format(episode_num))
        return MessageContainer(
            "Ошибка",
            "Эпизод не найден"
        )

    container = ObjectContainer(title2=locutils.make_title(episode_obj))
    container.add(plex.make_episode_item(play_episode, episode_url, episode_obj))

    return container


@route(PREFIX + '/soaps/{soap_id}/{season_num}/{episode_num}/play/{part}')
def episode_url(soap_id, season_num, episode_num, part):
    'provides specific url for episode'

    episode = soap.get_episode(soap_id, season_num, episode_num)
    if episode is None:
        Log.Critical("episode s{}e{} not found".format(season_num, episode_num))
        return MessageContainer(
            "Ошибка",
            "Эпизод не найден"
        )
    Log.Debug("[episode_url] episode: {}".format(json.dumps(episode, indent=2)))

    eid = episode['eid']
    ehash = episode['hash']
    token = Dict['token']

    if part == 1:
        return soap.mark_watched(eid)

    myhash = hashlib.md5(
        str(token) + str(eid) + str(soap_id) + str(ehash)
    ).hexdigest()
    params = {
        "what": "player",
        "do": "load",
        "token": token,
        "eid": eid,
        "hash": myhash
    }

    data = JSON.ObjectFromURL(
        "http://soap4.me/callback/",
        params,
        headers={
            'x-api-token': token,
            'Cookie': 'PHPSESSID=' + Dict['sid']
        })

    Log.Debug("player data: {}".format(json.dumps(data, indent=2)))

    if data["ok"] == 1:
        return Redirect("http://%s.soap4.me/%s/%s/%s/" % (data['server'], token, eid, myhash))
