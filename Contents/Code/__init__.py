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
ICON = 'icon.png'
BASE_URL = 'http://soap4.me/'
API_URL = 'http://soap4.me/api/'
LOGIN_URL = 'http://soap4.me/login/'
USER_AGENT = 'xbmc for soap'
LOGGEDIN = False
TOKEN = False
SID = ''


def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = TITLE
    DirectoryObject.thumb = R(ICON)

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
        return 2
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

            return 1
        else:
            LOGGEDIN = False
            Dict['sessionid'] = ""

            return 3


@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():

    oc = ObjectContainer()
    oc.add(
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
    oc.add(
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
    oc.add(
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
    oc.add(PrefsObject(title=u'Настройки', thumb=R('settings.png')))

    return oc


@route(PREFIX + '/soaps', filters={})
def Soaps(title2, filters={}):
    
    if filters != {}:
        Log.Debug("setting filters: %s".format(json.dumps(filters, indent=2)))
        Dict['filters'] = filters
    else:
        filters = Dict['filters']

    Log.Debug('filters: {}'.format(json.dumps(filters, indent=2)))

    logged = Login()
    if logged == 2:
        return MessageContainer(
            "Ошибка",
            "Ведите пароль и логин"
        )

    if logged == 3:
        return MessageContainer(
            "Ошибка",
            "Отказано в доступе"
        )

    dir = ObjectContainer(title2=title2.decode())
    dir.add(
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

    try:
        letter = filters['letter']
    except KeyError:
        letter = None

    Log.Debug("new: %s" % new)
    Log.Debug("letter: %s" % letter)

    # filters["new"] -> item["unwatched"] != None
    for items in soaps:
        if new and items["unwatched"] == None:
            continue

        if letter != None and items["title"][0] != letter:
            continue

        soap_title = items["title"]
        title = soap_title
        if filters["new"]:
            title = items["title"] + " (" + str(items["unwatched"]) + ")"

        summary = items["description"]
        poster = 'http://covers.s4me.ru/soap/big/' + items["sid"] + '.jpg'
        rating = float(items["imdb_rating"])
        summary = summary.replace('&quot;', '"')
        fan = 'http://thetvdb.com/banners/fanart/original/' + \
            items['tvdb_id'] + '-1.jpg'
        id = items["sid"]
        thumb = Function(utils.Thumb, url=poster)
        dir.add(
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
    return dir


@route(PREFIX + '/filters')
def Filters(title2):
    letters = utils.GetSoapsLetters()

    dir = ObjectContainer(title2=u'filter by starting letter')

    for letter in letters:
        dir.add(
            PopupDirectoryObject(
                key=Callback(
                    SetLetterFilter,
                    title2=title2,
                    letter=letter,
                ),
                title=letter,
            )
        )

    return dir


@route(PREFIX + '/filters/letter/{letter}')
def SetLetterFilter(letter, title2):
    filters = Dict['filters']
    filters['letter'] = letter

    Log.Debug('setting filters: {}'.format(json.dumps(filters, indent=2)))
    Dict['filters'] = filters
    Log.Debug('filters set')

    return Soaps(title2)


@route(PREFIX + '/soaps/{id}')
def show_seasons(id, soap_title):

    dir = ObjectContainer(title2=soap_title)
    url = API_URL + 'episodes/' + id
    data = utils.GET(url)
    season = {}
    useason = {}
    s_length = {}

    unwatched = Dict['filters']['new']
    Log.Debug('unwatched: {}'.format(unwatched))

    if unwatched:
        for episode in data:
            if episode['watched'] == None:
                if int(episode['season']) not in season:
                    season[int(episode['season'])] = episode['season_id']
                if int(episode['season']) not in useason.keys():
                    useason[int(episode['season'])] = []
                    useason[int(episode['season'])].append(
                        int(episode['episode']))
                elif int(episode['episode']) not in useason[int(episode['season'])]:
                    useason[int(episode['season'])].append(
                        int(episode['episode']))
    else:
        for episode in data:
            if int(episode['season']) not in season:
                season[int(episode['season'])] = episode['season_id']
                s_length[int(episode['season'])] = [episode['episode'], ]
            else:
                if episode['episode'] not in s_length[int(episode['season'])]:
                    s_length[int(episode['season'])].append(episode['episode'])

    for row in season:
        if unwatched:
            title = "%s сезон (%s)" % (row, len(useason[row]))
        else:
            title = "%s сезон" % (row)
        season_id = str(row)
        poster = "http://covers.s4me.ru/season/big/%s.jpg" % season[row]
        thumb = Function(utils.Thumb, url=poster)
        dir.add(
            SeasonObject(
                key=Callback(
                    show_episodes, sid=id, season=season_id,
                    soap_title=soap_title,
                ),
                episode_count=len(
                    s_length[row]) if s_length else len(useason[row]),
                show=soap_title,
                rating_key=str(row),
                title=title,
                thumb=thumb
            )
        )
    return dir


@route(PREFIX + '/soaps/{sid}/{season}', allow_sync=True)
def show_episodes(sid, season, soap_title):

    dir = ObjectContainer(title2=u'%s - %s сезон ' % (soap_title, season))
    url = API_URL + 'episodes/' + sid
    data = utils.GET(url)
    quality = Prefs["quality"]
    sort = Prefs["sorting"]
    show_only_hd = False

    if quality == "HD":
        for episode in data:
            if season == episode['season']:
                if episode['quality'] == '720p':
                    show_only_hd = True
                    break
    if sort != 'да':
        data = reversed(data)

    for row in data:
        if season == row['season']:

            if quality == "HD" and show_only_hd == True and row['quality'] != '720p':
                continue
            elif quality == "SD" and show_only_hd == False and row['quality'] != 'SD':
                continue
            else:
                if row['watched'] != None and Dict['filters']['new']:
                    continue
                else:
                    eid = row["eid"]
                    ehash = row['hash']
                    sid = row['sid']
                    title = ''
                    if not row['watched'] and not Dict['filters']['new']:
                        title += '* '
                    title += "S" + str(row['season']) \
                        + "E" + str(row['episode']) + " | " \
                        + row['quality'].encode('utf-8') + " | " \
                        + row['translate'].encode('utf-8') + " | " \
                        + row['title_en'].encode('utf-8').replace(
                            '&#039;', "'"
                        ).replace("&amp;", "&").replace('&quot;', '"')
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
                    dir.add(EpisodeObject(
                        key=Callback(play_episode, sid=sid,
                                     eid=eid, ehash=ehash, row=row),
                        rating_key='soap4me' + row["eid"],
                        title=title,
                        index=int(row['episode']),
                        thumb=thumb,
                        summary=summary,
                        items=[MediaObject(parts=parts)]
                    ))
    return dir


def play_episode(sid, eid, ehash, row, *args, **kwargs):
    oc = ObjectContainer()
    parts = [PartObject(key=Callback(episode_url, sid=sid,
                                     eid=eid, ehash=ehash, part=0))]
    if Prefs["mark_watched"] == 'да':
        parts.append(PartObject(key=Callback(
            episode_url, sid=sid, eid=eid, ehash=ehash, part=1)))
    oc.add(EpisodeObject(
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
    ))
    return oc


def episode_url(sid, eid, ehash, part):
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
        return Redirect('https://soap4.me/assets/blank/blank1.mp4')

    myhash = hashlib.md5(str(token) + str(eid) +
                         str(sid) + str(ehash)).hexdigest()
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
