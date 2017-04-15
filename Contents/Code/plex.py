
def makeMenuItem(callback, title, filters):
    return DirectoryObject(
        key=Callback(callback, title2=title, filters=filters),
        title=title
    )


def make_tvshow_item(callback, tvshow):
    soap_title = tvshow["title"]
    title = soap_title
    if Dict['filters']['new']:
        title += " (" + str(tvshow["unwatched"]) + ")"

    summary = tvshow["description"]
    poster = 'http://covers.s4me.ru/soap/big/' + tvshow["sid"] + '.jpg'
    rating = float(tvshow["imdb_rating"])
    summary = summary.replace('&quot;', '"')
    fan = 'http://thetvdb.com/banners/fanart/original/' + \
        tvshow['tvdb_id'] + '-1.jpg'
    soap_id = tvshow["sid"]
    thumb = Function(utils.Thumb, url=poster)

    Log.Debug('made item for {}'.format(title))

    return TVShowObject(
        key=Callback(
            callback, soap_id=soap_id, soap_title=soap_title,
        ),
        rating_key=str(soap_id),
        title=title,
        summary=summary,
        art=fan,
        rating=rating,
        thumb=thumb
    )


def make_season_item(callback, soap_id, soap_title, season_num, season_id, episodes):
    title = "%s сезон" % (season_num)
    if Dict['filters']['new']:
        title = "%s сезон (%s)" % (season_num, len(episodes[season_num]))

    seasonStr = str(season_num)
    poster = "http://covers.s4me.ru/season/big/%s.jpg" % season_id
    thumb = Function(utils.Thumb, url=poster)

    return SeasonObject(
        key=Callback(
            callback,
            soap_id=soap_id,
            season_num=seasonStr,
            soap_title=soap_title,
        ),
        episode_count=len(episodes[season_num]),
        show=soap_title,
        rating_key=str(season_num),
        title=title,
        thumb=thumb
    )

def make_episode_parts(url_callback, soap_id, season_num, episode_num):
    parts = [
        PartObject(
            key=Callback(
                url_callback,
                soap_id=soap_id,
                season_num=season_num,
                episode_num=episode_num,
                part=0
            )
        )
    ]

    if Prefs["mark_watched"] == 'да':
        parts.append(
            PartObject(
                key=Callback(
                    url_callback,
                    soap_id=soap_id,
                    season_num=season_num,
                    episode_num=episode_num,
                    part=1
                )
            )
        )

    return parts


def make_episode_item(play_callback, url_callback, episode):
    eid = episode["eid"]
    Log.Debug("EPISODE ID: {}".format(eid))
    soap_id = episode['sid']
    season_num = episode['season']
    episode_num = episode['episode']

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
        title=utils.make_title(episode),
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
                parts=make_episode_parts(url_callback, soap_id, season_num, episode_num)
            )
        ]
    )
