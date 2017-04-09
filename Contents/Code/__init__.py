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
    container.add(
        DirectoryObject(
            key=Callback(
                Soaps, title2=u'Все сериалы', filters={
                    "my": False,
                    "new": False,
                }
            ),
            title=u'Все сериалы'
        )
    )
    container.add(
        DirectoryObject(
            key=Callback(
                Soaps, title2=u'Я смотрю', filters={
                    "my": True,
                    "new": False,
                }
            ),
            title=u'Я смотрю'
        )
    )
    container.add(
        DirectoryObject(
            key=Callback(
                Soaps, title2=u'Новые эпизоды', filters={
                    "my": True,
                    "new": True,
                }
            ),
            title=u'Новые эпизоды'
        )
    )
    container.add(PrefsObject(title=u'Настройки', thumb=R('settings.png')))

    return container


@route(PREFIX + '/filters')
def Filters(title2):
    letters = utils.GetSoapsLetters()

    container = ObjectContainer(title2=u'Filters')

    container.add(
        PopupDirectoryObject(
            key=Callback(
                StartsWithFilters,
                title2=title2,
            ),
            title=u'Starts with',
        )
    )

    return container

@route(PREFIX + '/filters/letter')
def StartsWithFilters(title2):
    letters = utils.GetSoapsLetters()

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
    else:
        filters = Dict['filters']

    Log.Debug('filters: {}'.format(json.dumps(filters, indent=2)))

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

    soaps = utils.GetSoaps()

    try:
        new = filters['new']
    except KeyError:
        new = False

    if new:
        soaps = [x for x in soaps if x['unwatched'] != None]

    try:
        letter = filters['letter']
    except KeyError:
        letter = None

    if letter != None:
        soaps = [x for x in soaps if x['title'][0] == letter]

    for items in soaps:
        soap_title = items["title"]
        title = soap_title
        if new:
            title = items["title"] + " (" + str(items["unwatched"]) + ")"

        summary = items["description"]
        poster = 'http://covers.s4me.ru/soap/big/' + items["sid"] + '.jpg'
        rating = float(items["imdb_rating"])
        summary = summary.replace('&quot;', '"')
        fan = 'http://thetvdb.com/banners/fanart/original/' + \
            items['tvdb_id'] + '-1.jpg'
        id = items["sid"]
        thumb = Function(utils.Thumb, url=poster)

        container.add(
            TVShowObject(
                key=Callback(
                    show_seasons, id=id, soap_title=soap_title,
                ),
                rating_key=str(id),
                title=title,
                summary=summary,
                art=fan,
                rating=rating,
                thumb=thumb
            )
        )
    return container


@route(PREFIX + '/soaps/{id}')
def show_seasons(id, soap_title):

    container = ObjectContainer(title2=soap_title)
    episodes = utils.GetEpisodes(id)

    season = {}
    useason = {}

    new = Dict['filters']['new']

    if new:
        episodes = [x for x in episodes if x['watched'] == None]

    for episode in episodes:
        seasonNum = int(episode['season'])
        episodeNum = int(episode['episode'])

        if seasonNum not in season:
            season[seasonNum] = episode['season_id']

        if seasonNum not in useason.keys():
            useason[seasonNum] = []

        if episodeNum not in useason[seasonNum]:
            useason[seasonNum].append(episodeNum)

    for row in season:
        title = "%s сезон" % (row)
        if new:
            title = "%s сезон (%s)" % (row, len(useason[row]))

        season_id = str(row)
        poster = "http://covers.s4me.ru/season/big/%s.jpg" % season[row]
        thumb = Function(utils.Thumb, url=poster)
        container.add(
            SeasonObject(
                key=Callback(
                    show_episodes, sid=id, season=season_id,
                    soap_title=soap_title,
                ),
                episode_count=len(useason[row]),
                show=soap_title,
                rating_key=str(row),
                title=title,
                thumb=thumb
            )
        )
    return container


@route(PREFIX + '/soaps/{sid}/{season}', allow_sync=True)
def show_episodes(sid, season, soap_title):

    container = ObjectContainer(title2=u'%s - %s сезон ' % (soap_title, season))
    episodes = utils.GetEpisodes(sid)
    quality = Prefs["quality"]
    sort = Prefs["sorting"]
    show_only_hd = False

    episodes = [x for x in episodes if x['season'] == season]

    if quality == "HD":
        for episode in episodes:
            Log.Debug('episode: {}'.format(json.dumps(episode, indent=2)))
            if season == episode['season']:
                if episode['quality'] == '720p':
                    show_only_hd = True
                    break

    if quality == 'HD' and show_only_hd:
        episodes = [x for x in episodes if x['quality'] == '720p']

    if quality == 'SD' and not show_only_hd:
        episodes = [x for x in episodes if x['quality'] == 'SD']

    if Dict['filters']['new']:
        episodes = [x for x in episodes if x['watched'] == None]

    Log.Debug('sorting: {}'.format(sort))
    if sort != 'да':
        Log.Debug("reversing episodes")
        episodes = reversed(episodes)

    for row in episodes:
        eid = row["eid"]
        ehash = row['hash']
        sid = row['sid']

        title = utils.MakeTitle(row)
        poster = "http://covers.s4me.ru/season/big/%s.jpg" % row['season_id']
        summary = row['spoiler']
        thumb = Function(utils.Thumb, url=poster)
        parts = [
            PartObject(
                key=Callback(
                    episode_url,
                    sid=sid,
                    eid=eid,
                    ehash=ehash,
                    part=0
                )
            )
        ]
        if Prefs["mark_watched"] == 'да':
            parts.append(
                PartObject(
                    key=Callback(
                        episode_url,
                        sid=sid,
                        eid=eid,
                        ehash=ehash,
                        part=1
                    )
                )
            )

        container.add(EpisodeObject(
            key=Callback(
                play_episode,
                sid=sid,
                eid=eid,
                ehash=ehash,
                row=row
            ),
            rating_key='soap4me' + row["eid"],
            title=title,
            index=int(row['episode']),
            thumb=thumb,
            summary=summary,
            items=[MediaObject(parts=parts)]
        ))
    return container


def play_episode(sid, eid, ehash, row, *args, **kwargs):
    container = ObjectContainer()
    parts = [
        PartObject(
            key=Callback(
                episode_url,
                sid=sid,
                eid=eid,
                ehash=ehash,
                part=0
            )
        )
    ]
    if Prefs["mark_watched"] == 'да':
        parts.append(PartObject(
            key=Callback(
                episode_url,
                sid=sid,
                eid=eid,
                ehash=ehash,
                part=1
            )
        ))

    container.add(
        EpisodeObject(
            key=Callback(play_episode, sid=sid, eid=eid, ehash=ehash, row=row),
            rating_key='soap4me' + row["eid"],
            items=[MediaObject(
                video_resolution=720 if row['quality'].encode(
                    'utf-8') == '720p' else 400,
                video_codec=VideoCodec.H264,
                audio_codec=AudioCodec.AAC,
                container=Container.MP4,
                optimized_for_streaming=True,
                audio_channels=2,
                parts=parts
            )]
        )
    )
    return container


def episode_url(sid, eid, ehash, part):
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

