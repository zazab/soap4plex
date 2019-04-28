# -*- coding: utf-8 -*-
"""plex module"""

import hashlib
import locutils

ICON = 'icon.png'


def thumb(url):
    """
    if url specified, returns it wrapped in Data objec.
    if no url provided, returns default icon
    """

    if url == '':
        return Redirect(R(ICON))
    else:
        try:
            data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
            return DataObject(data, 'image/jpeg')
        except Exception:
            return Redirect(R(ICON))


def make_menu_item(callback, title, filters):
    """generates simple menu entry"""
    return DirectoryObject(
        key=Callback(callback, title2=title, filters=filters),
        title=title
    )


def make_tv_show_item(callback, tv_show):
    """generates tv show object"""
    soap_title = tv_show["title"]
    title = soap_title
    if Dict['filters']['new']:
        title += " (" + str(tv_show["unwatched"]) + ")"

    summary = tv_show["description"]
    poster = 'http://covers.s4me.ru/soap/big/' + tv_show["sid"] + '.jpg'
    rating = float(tv_show["imdb_rating"])
    summary = summary.replace('&quot;', '"')
    fan = 'http://thetvdb.com/banners/fanart/original/' + \
          tv_show['tvdb_id'] + '-1.jpg'
    soap_id = tv_show["sid"]

    return TVShowObject(
        key=Callback(
            callback, soap_id=soap_id, soap_title=soap_title,
        ),
        rating_key=str(soap_id),
        title=title,
        summary=summary,
        art=fan,
        rating=rating,
        thumb=Function(thumb, url=poster)
    )


def make_season_item(callback, soap_id, soap_title, season_num, season_id, episodes):
    """generates season object"""

    title = "%s сезон" % season_num
    if Dict['filters']['new']:
        title = "%s сезон (%s)" % (season_num, len(episodes[season_num]))

    season_str = str(season_num)
    poster = "http://covers.s4me.ru/season/big/%s.jpg" % season_id

    return SeasonObject(
        key=Callback(
            callback,
            soap_id=soap_id,
            season_num=season_str,
            soap_title=soap_title,
        ),
        episode_count=len(episodes[season_num]),
        show=soap_title,
        rating_key=str(season_num),
        title=title,
        thumb=Function(thumb, url=poster)
    )


def play_episode(token, eid, soap_id, ehash):
    hashed = hashlib.md5(
        str(token) + str(eid) + str(soap_id) + str(ehash)
    ).hexdigest()
    params = {
        "what": "player",
        "do": "load",
        "token": token,
        "eid": eid,
        "hash": hashed
    }

    data = JSON.ObjectFromURL(
        "http://soap4.me/callback/",
        params,
        headers={
            'x-api-token': token,
            'Cookie': 'PHPSESSID=' + Dict['sid']
        })

    if data["ok"] == 1:
        url = "http://%s.soap4.me/%s/%s/%s/" % (data['server'], token, eid, hashed)
        return Redirect(url)

    return MessageContainer("can't get url")


def make_episode_parts(mark_watched_callback, soap_id, eid, ehash):
    """generates episode parts"""

    parts = [
        PartObject(
            key=Callback(
                play_episode,
                token=Dict['token'],
                eid=eid,
                soap_id=soap_id,
                ehash=ehash
            )
        )
    ]

    if Prefs["mark_watched"] == 'да':
        parts.append(
            PartObject(
                key=Callback(
                    mark_watched_callback,
                    eid=eid,
                ),
                duration=1,
            )
        )

    return parts


def make_episode_item(play_callback, mark_watched_callback, episode):
    """generates episode object"""

    eid = episode["eid"]
    soap_id = episode['sid']
    season_num = episode['season']
    episode_num = episode['episode']
    episode_hash = episode['hash']

    resolution = 400
    if episode['quality'].encode('utf-8') == '720p':
        resolution = 720

    return EpisodeObject(
        key=Callback(
            play_callback,
            soap_id=soap_id,
            season_num=season_num,
            episode_num=episode_num,
        ),
        rating_key='soap4me' + eid,
        title=locutils.make_title(episode),
        index=int(episode['episode']),
        summary=episode['spoiler'],
        items=[
            MediaObject(
                video_resolution=resolution,
                video_codec=VideoCodec.H264,
                audio_codec=AudioCodec.AAC,
                container=Container.MP4,
                optimized_for_streaming=True,
                audio_channels=1,
                parts=make_episode_parts(mark_watched_callback, soap_id, eid, episode_hash)
            )
        ]
    )
