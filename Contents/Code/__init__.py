# -*- coding: utf-8 -*-

# created by sergio
# updated by kestl1st@gmail.com (@kestl) v.1.2.3 2016-08-01
# updated by sergio v.1.2.2 2014-08-28

import re
import urllib2
import base64
import hashlib
import md5
import urllib
import calendar
from datetime import *
import time
import json

import utils
import soap
import plex

VERSION = 2.0
PREFIX = "/video/soap4meNew"
TITLE = 'soap4.me (new)'
ART = 'art.png'
API_URL = 'http://soap4.me/api/'
LOGIN_URL = 'http://soap4.me/login/'
USER_AGENT = 'xbmc for soap'
LOGGEDIN = False
TOKEN = False
SID = ''


def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = TITLE
    DirectoryObject.thumb = R(utils.ICON)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = USER_AGENT
    HTTP.Headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    HTTP.Headers['Accept-Encoding'] = 'gzip,deflate,sdch'
    HTTP.Headers['Accept-Language'] = 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3'
    HTTP.Headers['x-api-token'] = TOKEN


def Login():
    global LOGGEDIN, SID, TOKEN

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
        except Exception as e:
            Log.Debug("can't log in: {}".format(e))
            obj = []
            LOGGEDIN = False
            return 3

        SID = obj['sid']
        TOKEN = obj['token']
        if len(TOKEN) > 0:
            LOGGEDIN = True
            Dict['sid'] = SID
            Dict['token'] = TOKEN

            return None
        else:
            LOGGEDIN = False
            Dict['sessionid'] = ""

            return MessageContainer(
                "Ошибка",
                "Отказано в доступе"
            )


@handler(PREFIX, TITLE, thumb=utils.ICON, art=ART)
def MainMenu():

    container = ObjectContainer()
    container.add(plex.makeMenuItem(
        Soaps,
        title=u'Все сериалы',
        filters={
            'my': False,
            'new': False
        }
    ))
    container.add(plex.makeMenuItem(
        Soaps,
        title=u'Я смотрю',
        filters={
            "my": True,
            "new": False,
        }
    ))
    container.add(plex.makeMenuItem(
        Soaps,
        title=u'Новые эпизоды',
        filters={
            "my": True,
            "new": True,
        }
    ))

    container.add(PrefsObject(title=u'Настройки', thumb=R('settings.png')))

    return container


@route(PREFIX + '/filters')
def Filters(title2):
    '''
    letters = soap.GetSoapsLetters()

    container = ObjectContainer(title2=u'Filters')
    container.add(
        plex.makePopupDirectory(
            StartsWithFilters,
            title=u'Starts with',
        )
    )
    '''

    return StartsWithFilters(title2)

@route(PREFIX + '/filters/letter')
def StartsWithFilters(title2):
    letters = soap.GetSoapsLetters()

    container = ObjectContainer(title2=u'Starts With')

    for letter in letters:
        container.add(
            PopupDirectoryObject(
                key=Callback(
                    SetLetterFilter,
                    title2=title2,
                    letter=letter,
                ),
                title=letter,
            )
        )

    return container


@route(PREFIX + '/filters/letter/{letter}')
def SetLetterFilter(letter, title2):
    filters = Dict['filters']
    filters['letter'] = letter

    Log.Debug('setting filters: {}'.format(json.dumps(filters, indent=2)))
    Dict['filters'] = filters
    Log.Debug('filters set')

    return Soaps(title2)


@route(PREFIX + '/soaps', filters={})
def Soaps(title2, filters={}):

    if filters != {}:
        Log.Debug("setting filters: %s".format(json.dumps(filters, indent=2)))
        Dict['filters'] = filters

    error = Login()
    if error != None:
        return error

    container = ObjectContainer(title2=title2.decode())
    container.add(
        PopupDirectoryObject(
            key=Callback(Filters, title2=title2),
            title=u'Фильтровать'
        )
    )

    soaps = soap.get_soaps()
    soaps = utils.filter_by_letter(soaps)

    for item in soaps:

        container.add(plex.make_tvshow_item(show_seasons, item))
    return container


@route(PREFIX + '/soaps/{soap_id}')
def show_seasons(soap_id, soap_title):
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


@route(PREFIX + '/soaps/{sid}/{season}', allow_sync=True)
def show_episodes(soap_id, season, soap_title):
    container = ObjectContainer(title2=u'%s - %s сезон ' % (soap_title, season))

    episodes = soap.get_season_episodes(soap_id, season)
    episodes = utils.filter_episodes_by_quality(episodes)

    for episode in episodes:
        container.add(plex.make_episode_item(play_episode, episode_url, episode))

    return container


def play_episode(episode, *args, **kwargs):
    Log.Debug('args: {}'.format(json.dumps(args, indent=2)))
    Log.Debug('kwargs: {}'.format(json.dumps(kwargs, indent=2)))
    container = ObjectContainer(title2=utils.make_title(episode))

    container.add(plex.make_episode_item(play_episode, episode_url, episode))

    return container


def episode_url(sid, eid, ehash, part, *args, **kwargs):
    Log.Debug("[episode url] sid: {}; eid: {}; ehash: {}; part: {}".format(
        sid, eid, ehash, part,
    ))
    token = Dict['token']
    if part == 1:
        params = {"what": "mark_watched", "eid": eid, "token": token}
        data = JSON.ObjectFromURL(
            "http://soap4.me/callback/",
            params,
            headers={
                'x-api-token': Dict['token'],
                'Cookie': 'PHPSESSID=' + Dict['sid']
            }
        )
        Log.Debug("marked: {}".format(json.dumps(data, indent=2)))
        return Redirect('https://soap4.me/assets/blank/blank1.mp4')

    myhash = hashlib.md5(
        str(token) + str(eid) + str(sid) + str(ehash)
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
            'x-api-token': Dict['token'],
            'Cookie': 'PHPSESSID=' + Dict['sid']
        })
    #Log.Debug('!!!!!!!!!!!!!!!!!! === ' + str(data))
    if data["ok"] == 1:
        return Redirect("http://%s.soap4.me/%s/%s/%s/" % (data['server'], token, eid, myhash))

