import utils

API_URL = 'http://soap4.me/api/'

def GetSoaps():
    filters = Dict['filters']

    url = API_URL + 'soap/'
    if filters['my']:
        url += 'my/'

    soaps = utils.GET(url)
    soaps = sorted(soaps, key=lambda k: k['title'])

    return soaps


def GetEpisodes(id):
    filters = Dict['filters']

    url = API_URL + 'episodes/' + id
    episodes = utils.GET(url)

    return episodes


def GetSoapsLetters():
    soaps = GetSoaps()

    letters = []
    for item in soaps:
        letter = item['title'][0]
        if letter not in letters:
            letters.append(letter)
    
    return letters

