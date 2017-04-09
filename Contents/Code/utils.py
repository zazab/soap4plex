API_URL = 'http://soap4.me/api/'
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


def GetSoaps():
    filters = Dict['filters']

    url = API_URL + 'soap/'
    if filters['my']:
        url = API_URL + 'soap/my/'

    soaps = GET(url)
    soaps = sorted(soaps, key=lambda k: k['title'])

    return soaps


def GetEpisodes(id):
    filters = Dict['filters']

    url = API_URL + 'episodes/' + id
    episodes = GET(url)

    return episodes


def GetSoapsLetters():
    soaps = GetSoaps()

    letters = []
    for item in soaps:
        letter = item['title'][0]
        if letter not in letters:
            letters.append(letter)
    
    return letters


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
