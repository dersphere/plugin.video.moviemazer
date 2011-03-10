# Moviemazer XBMC Addon
# written by Tristan Fischer (sphere)
#
# If you have suggestions or problems: write me.
#
# Mail: sphere@dersphere.de
#
# Special Thanks to the website www.moviemaze.de

# Import Python stuff

import urllib
import urllib2
import re
import os
import sys
import time
from shutil import copyfile

# Import XBMC Stuff

import xbmcplugin
import xbmcgui
import xbmcaddon


# Creating some default variables and objects

Addon = xbmcaddon.Addon('plugin.video.moviemazer')
MAIN_URL = 'http://www.moviemaze.de'

ADDON_ID = Addon.getAddonInfo('id')
CACHE_DIR = 'special://profile/addon_data/%s/cache/' % ADDON_ID
IMAGE_DIR = 'special://home/addons/%s/resources/images/' % ADDON_ID

GetSetting = Addon.getSetting
SetSetting = Addon.setSetting
Language = Addon.getLocalizedString
Handle = int(sys.argv[1])
ProgressDialog = xbmcgui.DialogProgress()


# Functions for getting a list of dicts containing movie headers like ID and title

def get_top_ten_movies():
    returnmovies = []
    fullurl = '%s/media/trailer/' % MAIN_URL
    link = get_cached_url(fullurl, 'mainpage.cache', GetSetting('cache_movies_list'))
    matchtopten = re.compile('<tr><td valign="top" align="right"><b>([0-9]+)</b></td><td width=100% style="text-align:left;"><a href="/media/trailer/([0-9]+),(?:[0-9]+?,)?([^",]+?)">([^<]+)</a> <span class="small_grey">\(([^<]+)\)</span></td></tr>').findall(link)
    for rank, movieid, urlend, title, trailerkind in matchtopten:
        movie = {'movieid': movieid,
                 'title': title,
                 'urlend': urlend,
                 'rank': '%s. ' % rank,
                 'date': ''}
        returnmovies.append(movie)
    return returnmovies


def get_recent_movies():
    returnmovies = []
    fullurl = '%s/media/trailer/' % MAIN_URL
    link = get_cached_url(fullurl, 'mainpage.cache', GetSetting('cache_movies_list'))
    matchtrecentupdates = re.compile('<td(?: valign="top" style="text-align:left;"><b style="white-space: nowrap;">([^<]*)</b)?></td><td width=100% style="text-align:left;"><a href="/media/trailer/([0-9]+),(?:[0-9]+?,)?([^",]+?)">([^<]+)</a> <span class="small_grey">\(([^<]+)\)</span></td></tr>').findall(link)
    for date, movieid, urlend, title, trailerkind in matchtrecentupdates:
        if date != '':
            lastdate = date
        else:
            date = lastdate
        datearray = date.split(' ')
        months_de_short = ['', 'Jan', 'Feb', 'M\xe4r', 'Apr', 'Mai', 'Juni', 'Juli', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
        try:
            date = ' (%s%02d.%s)' % (datearray[0], months_de_short.index(datearray[1]), '2011')  # Fixme: dirty hack :(
        except:
            date = ''
        movie = {'movieid': movieid,
                 'title': title,
                 'urlend': urlend,
                 'rank': '',
                 'date': date}
        returnmovies.append(movie)
    return returnmovies


def get_current_movies():
    returnmovies = []
    fullurl = '%s/media/trailer/' % MAIN_URL
    link = get_cached_url(fullurl, 'mainpage.cache', GetSetting('cache_movies_list'))
    matchtacttrailers = re.compile('<tr><td(?: valign="top"><b>[A-Z0-9]</b)?></td><td style="text-align:left;"><a href="/media/trailer/([0-9]+),(?:[0-9]+?,)?([^",]+?)">([^<]+)</a></td></tr>').findall(link)
    for movieid, urlend, title in matchtacttrailers:
        movie = {'movieid': movieid,
                 'title': title,
                 'urlend': urlend,
                 'rank': '',
                 'date': ''}
        returnmovies.append(movie)
    return returnmovies


# Function to get a dict of detailed movie information like coverURL, plot and genres

def get_movie_infos(movieid, urlend='movie.html'):
    returnmovie = {'movieid': movieid,
                   'title': '',
                   'otitle': '',
                   'coverurl': '',
                   'plot': '',
                   'genres': '',
                   'date': ''}
    fullurl = '%s/media/trailer/%s,15,%s' % (MAIN_URL,
                                             movieid,
                                             urlend)
    cachefile = 'id%s.cache' % movieid
    link = get_cached_url(fullurl, cachefile, GetSetting('cache_movie_info'))
    titlematch = re.compile('<h1>(.+?)</h1>.*<h2>\((.+?)\)</h2>', re.DOTALL).findall(link)
    for title, otitle in titlematch:
        returnmovie.update({'title': title, 'otitle': otitle})
    covermatch = re.compile('src="([^"]+?)" width="150"').findall(link)
    for coverurl in covermatch:
        if coverurl != '/filme/grafiken/kein_poster.jpg':
            returnmovie.update({'coverurl': MAIN_URL + coverurl})
    plotmatch = re.compile('WERDEN! -->(.+?)</span>').findall(link)
    for plot in plotmatch:
        plot = re.sub('<[^<]*?/?>', '', plot)
        returnmovie.update({'plot': plot})
    releasedatematch = re.compile('Dt. Start:</b> ([0-9]+.+?)<img').findall(link)
    for releasedateugly in releasedatematch:
        datearray = releasedateugly.split(' ')
        months_de_long = ['', 'Januar', 'Februar', 'M\xe4rz', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
        date = ' (%s%02d.%s)' % (datearray[0], months_de_long.index(datearray[1]), '2011')  # Fixme: dirty hack :(
        returnmovie.update({'date': date})
    genresmatch = re.compile('<b style="font-weight:bold;">Genre:</b> (.+?)<br />', re.DOTALL).findall(link)
    for allgenres in genresmatch:
        returnmovie.update({'genres': allgenres})
    return returnmovie


# Function to get a list of dicts which contains trailer- URL, resolution, releasedate

def get_movie_trailers(movieid, urlend='movie.html'):
    returntrailers = []
    fullurl = '%s/media/trailer/%s,15,%s' % (MAIN_URL,
                                             movieid,
                                             urlend)
    cachefile = 'id%s.cache' % movieid
    link = get_cached_url(fullurl, cachefile, GetSetting('cache_movie_info'))
    matchtrailerblock = re.compile('<table border=0 cellpadding=0 cellspacing=0 align=center width=100%><tr><td class="standard">.+?<b style="font-weight:bold;">(.+?)</b><br />\(([0-9:]+) Minuten\)(.+?</td></tr></table><br /></td></tr></table><br />)', re.DOTALL).findall(link)
    for trailername, duration, trailerblock in matchtrailerblock:
        matchlanguageblock = re.compile('alt="Sprache: (..)">(.+?)>([^<]+)</td></tr></table></td>', re.DOTALL).findall(trailerblock)
        for language, languageblock, date in matchlanguageblock:
            datearray = date.split(' ')
            months_de_short = ['', 'Jan', 'Feb', 'M\xe4rz', 'Apr', 'Mai', 'Juni', 'Juli', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
            try:
                date = datearray[0] + str(months_de_short.index(datearray[1])).zfill(2) + '.2011'  # fixme: this could be made better, no idea how :)
            except:
                date = ''
            matchtrailer = re.compile('generateDownloadLink\("([^"]+_([0-9]+)\.(?:mov|mp4)\?down=1)"\)').findall(languageblock)
            for trailerurl, resolution in matchtrailer:
                trailer = {'trailername': trailername,
                           'duration': duration,
                           'language': language,
                           'resolution': resolution,
                           'date': date,
                           'trailerurl': MAIN_URL + trailerurl}
                returntrailers.append(trailer)
    return returntrailers


# Functions to get the informations for xbmc

def show_categories():
    add_dir(Language(30003), 3, os.path.join(IMAGE_DIR, 'database.png'))  # Current
    add_dir(Language(30001), 1, os.path.join(IMAGE_DIR, 'ranking.png'))  # TopTen
    add_dir(Language(30002), 2, os.path.join(IMAGE_DIR, 'schedule.png'))  # Recent
    end_dir()


def show_top_ten_movies():
    toptenmovies = get_top_ten_movies()
    show_movies(toptenmovies)
    end_dir()


def show_recent_movies():
    recentmovies = get_recent_movies()
    show_movies(recentmovies)
    end_dir()


def show_current_movies():
    currentmovies = get_current_movies()
    show_movies(currentmovies)
    end_dir()


# Functions to show the informations in xbmc

def show_movies(movies):
    counter = 0
    ProgressDialog = xbmcgui.DialogProgress()
    ProgressDialog.create(Language(30020), '%s %s' % (str(len(movies)), Language(30021)))
    ProgressDialog.update(0)
    for movie in movies:
        movieinfo = get_movie_infos(movieid=movie['movieid'], urlend=movie['urlend'])
        title = '%s%s%s' % (movie['rank'], movieinfo['title'], movie['date'])
        add_movie(title=title,
                  movieid=movieinfo['movieid'],
                  coverurl=movieinfo['coverurl'],
                  plot=movieinfo['plot'],
                  otitle=movieinfo['otitle'],
                  genres=movieinfo['genres'],
                  releasedate=movieinfo['date'],
                  playcount=get_playcount(movie['movieid']))
        counter += 1
        ProgressDialog.update(100 * counter / len(movies),
                              '%s %s' % (str(len(movies)), Language(30021)),  # x movies have to be cached
                              '%s: %s' % (Language(30022), movieinfo['title'].decode('utf-8', 'ignore')))  # Loading : y
        if ProgressDialog.iscanceled():
            break
    ProgressDialog.close()


# Functions to add single Folders to the xbmc screen and tell xbmc that all is there

def add_dir(dirname, cat, iconimage):
    u = '%s?cat=%s' % (sys.argv[0], str(cat))
    liz = xbmcgui.ListItem(dirname,
                           iconImage='DefaultVideo.png',
                           thumbnailImage=iconimage)
    liz.setInfo(type='Video',
                infoLabels={'Title': dirname})
    ok = xbmcplugin.addDirectoryItem(handle=Handle,
                                     url=u,
                                     listitem=liz,
                                     isFolder=True)


def add_movie(title, movieid, coverurl='', plot='', otitle='', genres='', releasedate='', playcount=0):
    u = '%s?cat=%s&movieid=%s' % (sys.argv[0], str(cat), movieid)
    liz = xbmcgui.ListItem(title,
                           iconImage='DefaultVideo.png',
                           thumbnailImage=coverurl)
    liz.setInfo(type='Video',
                infoLabels={'Title': title,
                            'Tagline': '%s: %s' % (Language(30030), releasedate),
                            'Plot': plot,
                            'Studio': otitle,  # fixme: there is no label for "original title"
                            'Genre': genres})
    liz.setProperty('releasedate', releasedate)
    if int(playcount) > 0:
        liz.setInfo(type='Video', infoLabels={'overlay': 7})
    contextmenu = [(Language(30231), 'XBMC.RunPlugin(%s&mode=guess)' % u),
                   (Language(30232), 'XBMC.RunPlugin(%s&mode=ask)' % u),
                   (Language(30233), 'XBMC.Action(Info)'),
                   (Language(1045), 'XBMC.RunPlugin(%s&GetSettings=open)' % u)]
    liz.addContextMenuItems(contextmenu, True)
    xbmcplugin.addDirectoryItem(handle=Handle,
                                url=u,
                                listitem=liz,
                                isFolder=False)


def end_dir():
    xbmcplugin.addSortMethod(Handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(Handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(Handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(Handle, cacheToDisc=True)


# Functions to choose a trailer - ask user or guess with the preferred GetSettings

def ask_for_trailer(movietrailers):
    movieinfo = get_movie_infos(movieid)
    backlabel = '--> %s <--' % Language(30011)  # Back, there is no 'cancel' in Dialog.select :(
    trailercaptionlist = [backlabel]
    trailerurllist = ['']
    for trailer in movietrailers:
        trailercaption = '%s - %s - %s (%s)' % (trailer['trailername'],
                                                trailer['language'],
                                                trailer['resolution'],
                                                trailer['date'])
        trailercaptionlist.append(trailercaption)
        trailerurllist.append(trailer['trailerurl'])
    Dialog = xbmcgui.Dialog()
    if len(trailercaptionlist) > 1:
        chosentrailer = Dialog.select(Language(30010), trailercaptionlist)
        if chosentrailer != 0:
            trailer = {'trailerurl': trailerurllist[chosentrailer],
                       'title': movieinfo['title'],
                       'studio': trailercaptionlist[chosentrailer],
                       'coverurl': movieinfo['coverurl']}
            return trailer
    else:
        Dialog.ok(movieinfo['title'], Language(30012))  # No Trailer found :(


def guess_pref_trailer(movietrailers):
    prefres = int(GetSetting('trailer_xres'))
    allres = ['1920', '1280', '1024', '848', '720', '640', '512', '480', '320']
    prefmovietrailers = []
    diff = 0
    if len(filter_dic(movietrailers, 'language', GetSetting('trailer_lang'))) > 0:
        movietrailers = filter_dic(movietrailers, 'language', GetSetting('trailer_lang'))
    while len(prefmovietrailers) == 0:
        searchres = prefres + diff
        if not searchres >= len(allres):
            prefmovietrailers = filter_dic(movietrailers, 'resolution', allres[searchres])
        if len(prefmovietrailers) == 0 and not diff == 0:
            searchres = prefres - diff
            if searchres >= 0:
                prefmovietrailers = filter_dic(movietrailers, 'resolution', allres[searchres])
        diff += 1
        if diff > len(allres) + 1:
            break
    prefmovietrailer = prefmovietrailers[len(prefmovietrailers) - 1]
    trailercaption = '%s - %s - %s (%s)' % (prefmovietrailer['trailername'],
                                            prefmovietrailer['language'],
                                            prefmovietrailer['resolution'],
                                            prefmovietrailer['date'])
    movieinfo = get_movie_infos(movieid)
    trailer = {'trailerurl': prefmovietrailer['trailerurl'],
               'title': movieinfo['title'],
               'studio': trailercaption,
               'coverurl': movieinfo['coverurl']}
    return trailer


# Function to play a Trailer

def play_trailer(trailerurl, movieid, title='', studio='', coverurl=''):
    liz = xbmcgui.ListItem(label=title,
                           iconImage='DefaultVideo.png',
                           thumbnailImage=coverurl)
    liz.setInfo(type='Video',
                infoLabels={'Title': title, 'Studio': studio})
    if GetSetting('play_mode') == '0':  # Setting is to download and then play the trailer
        ProgressDialog.create(Language(30025), Language(30026) % ('0', '?'), '%s (%s)' % (title, studio))
        ProgressDialog.update(0)
        trailerfile = re.search('.*/([^/]+)\?down=1', trailerurl).group(1)
        trailerfile = re.sub('[^\w\s.-]', '', '%s - %s' % (title, trailerfile))
        downloadpath = GetSetting('download_path')
        if downloadpath == '':
            downloadpath = CACHE_DIR
        filepath = downloadpath + trailerfile
        if not os.path.isfile(filepath):
            filepathtemp = filepath + '.tmp'
            urllib.urlretrieve(trailerurl, filepathtemp, update_progress_hook)
            copyfile(filepathtemp, filepath)
            os.remove(xbmc.translatePath(filepathtemp))
        trailerurl = filepath
        ProgressDialog.close()
    Player = xbmc.Player(xbmc.PLAYER_CORE_AUTO)
    Player.play(trailerurl, liz)
    set_playcount(movieid)


# Function to update the xbmc Dialog while downloading, inspired by the videomonkey addon :-)

def update_progress_hook(count, blocksize, totalsize):
    percent = int(float(count * blocksize * 100) / totalsize)
    kilofloat = float(1024)
    totalsizemb = "%.2f" % (totalsize / kilofloat / kilofloat)
    countmb = "%.2f" % (count * blocksize / kilofloat / kilofloat)
    ProgressDialog.update(percent, Language(30026) % (countmb, totalsizemb))
    if ProgressDialog.iscanceled():
        raise KeyboardInterrupt


# Helper Functions

def get_cached_url(url, filename, timetolive=1):
    requestheader = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.2.9) Gecko/20100824 Firefox/3.6.9'
    cachefilefullpath = CACHE_DIR + filename
    timetolive = int(timetolive) * 60 * 60  # timetolive Settings are in hours!
    if not os.path.isdir(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    try:
        cachefiledate = os.path.getmtime(cachefilefullpath)
    except:
        cachefiledate = 0
    if (time.time() - (timetolive)) > cachefiledate:
        req = urllib2.Request(url)
        req.add_header('User-Agent', requestheader)
        sock = urllib2.urlopen(req)
        link = sock.read()
        encoding = sock.headers['Content-type'].split('charset=')[1]
        outfile = open(cachefilefullpath, 'w')
        outfile.write(link)
        outfile.close()
    else:
        sock = open(cachefilefullpath, 'r')
        link = sock.read()
    sock.close()
    return link


def filter_dic(dic, key, value):
    return [d for d in dic if (d.get(key) == value)]


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


# Functions for get/set the user playcounts

def get_playcount(movieid):
    playcount = GetSetting('playcount-movieid=%s' % movieid)
    if not playcount:
        playcount = 0
    return playcount


def set_playcount(movieid):
    pc = int(get_playcount(movieid))
    pc += 1
    SetSetting('playcount-movieid=%s' % movieid, str(pc))


# Addon Standard Stuff - here the addon starts

params = get_params()

print 'MovieMazer Addon started with "%s"' % params

try:
    movieid = params['movieid']
except:
    movieid = ''

try:
    cat = int(params['cat'])
except:
    cat = None

try:
    mode = params['mode']
except:
    mode = None


startwith = int(GetSetting('start_with'))
if startwith != 0:
    if cat == None:
        cat = startwith
        add_dir(Language(30311), 0, os.path.join(IMAGE_DIR, 'trailer.png'))  # Categories


if movieid != '':
    trailer = None
    if mode == 'guess':
        trailer = guess_pref_trailer(get_movie_trailers(movieid))
    elif mode == 'ask':
        trailer = ask_for_trailer(get_movie_trailers(movieid))
    else:
        prefmode = GetSetting('pref_mode')
        if prefmode == '0':
            trailer = guess_pref_trailer(get_movie_trailers(movieid))
        elif prefmode == '1':
            trailer = ask_for_trailer(get_movie_trailers(movieid))
    if trailer != None:
        play_trailer(trailerurl=trailer['trailerurl'],
                     movieid=movieid,
                     title=trailer['title'],
                     studio=trailer['studio'],
                     coverurl=trailer['coverurl'])
    else:
        pass  # could be that user was asked to chose trailer but he hit "back"
elif cat == 1:
    show_top_ten_movies()
elif cat == 2:
    show_recent_movies()
elif cat == 3:
    show_current_movies()
else:
    show_categories()

print 'MovieMazer Addon ended'
