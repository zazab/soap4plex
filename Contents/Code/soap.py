import utils

API_URL = 'http://soap4.me/api/'

def get_soaps():
    filters = Dict['filters']

    url = API_URL + 'soap/'
    if filters['my']:
        url += 'my/'

    soaps = utils.GET(url)
    soaps = sorted(soaps, key=lambda k: k['title'])

    Log.Debug("got {} soaps".format(len(soaps)))

    return utils.filter_unwatched_soaps(soaps)


def get_episodes(soap_id):
    url = API_URL + 'episodes/' + soap_id
    episodes = utils.GET(url)

    return utils.filter_unwatched_episodes(episodes)


def get_season_episodes(soap_id, season):
    episodes = get_episodes(soap_id)

    if Prefs['sorting'] != 'да':
        episodes = reversed(episodes)

    return [x for x in episodes if x['season'] == season]


def GetSoapsLetters():
    soaps = get_soaps()

    letters = []
    for item in soaps:
        letter = item['title'][0]
        if letter not in letters:
            letters.append(letter)
    
    return letters

