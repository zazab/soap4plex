ICON = 'icon.png'

def Thumb(url):
    if url == '':
        return Redirect(R(ICON))
    else:
        try:
            data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
            return DataObject(data, 'image/jpeg')
        except:
            return Redirect(R(ICON))


def GET(url):
    return JSON.ObjectFromURL(
        url,
        headers={
            'x-api-token': Dict['token'],
            'Cookie': 'PHPSESSID=' + Dict['sid']
        },
        cacheTime=0
    )


def make_title(episode):
    new = ''
    if not episode['watched']:
        new = '* '

    season = 'S{}'.format(episode['season'])
    episodeString = 'E{}'.format(episode['episode'])
    quality = episode['quality'].encode('utf-8')
    translate = episode['translate'].encode('utf-8')
    title = episode['title_en'].encode('utf-8').replace('&#039;', "'")
    return '{}{}{} | {} | {} | {}'.format(
        new, season, episodeString,
        quality, translate, title,
    )


def filter_unwatched_soaps(soaps):
    watched = Dict['filters']['new']
    if watched:
        soaps = [x for x in soaps if x['unwatched'] is not None]
        Log.Debug('{} filtered soaps'.format(len(soaps)))

    return soaps


def filter_unwatched_episodes(episodes):
    watched = Dict['filters']['new']
    if watched:
        soaps = [x for x in episodes if x['watched'] is None]

    return soaps


def filter_by_letter(soaps):
    try:
        letter = Dict['filters']['letter']
    except KeyError:
        letter = None

    if letter != None:
        soaps = [x for x in soaps if x['title'][0] == letter]

    return soaps


def filter_episodes_by_quality(episodes):
    quality = Prefs["quality"]
    only_hd = False

    if quality == "HD":
        for episode in episodes:
            Log.Debug('episode: {}'.format(json.dumps(episode, indent=2)))
            if episode['quality'] == '720p':
                only_hd = True
                break

    if quality == 'HD' and only_hd:
        return [x for x in episodes if x['quality'] == '720p']

    return [x for x in episodes if x['quality'] == 'SD']
