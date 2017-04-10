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


def MakeTitle(episode):
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
