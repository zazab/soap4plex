API_URL = 'http://soap4.me/api/'

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

    obj = GET(url)
    obj = sorted(obj, key=lambda k: k['title'])

    return obj


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
