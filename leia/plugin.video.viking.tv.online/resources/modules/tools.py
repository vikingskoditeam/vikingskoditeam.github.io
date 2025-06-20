import os,re,sys,json,base64,string,requests,shutil,socket
from resources.modules import client,control
import six
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
from six.moves import urllib_parse, urllib_request, http_cookiejar
ADDONTITLE     = 'Flechanegra'

def getKodiVersion():
    return int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])

def regex_from_to(text, from_string, to_string, excluding=True):
	if excluding:
		try: r = re.search("(?i)" + from_string + "([\S\s]+?)" + to_string, text).group(1)
		except: r = ''
	else:
		try: r = re.search("(?i)(" + from_string + "[\S\s]+?" + to_string + ")", text).group(1)
		except: r = ''
	return r


def regex_get_all(text, start_with, end_with):
	r = re.findall("(?i)(" + start_with + "[\S\s]+?" + end_with + ")", text)
	return r
	
def addDir(name,url,mode,iconimage,fanart,description):
	u=sys.argv[0]+"?url="+urllib_parse.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib_parse.quote_plus(name)+"&iconimage="+urllib_parse.quote_plus(iconimage)+"&description="+urllib_parse.quote_plus(description)
	ok=True
	xbmc.log(str(u))
	liz=xbmcgui.ListItem(name)
	liz.setArt({ 'thumb': iconimage, 'icon': iconimage, 'fanart': fanart}) 
	liz.setInfo( type="Video", infoLabels={"Title": name,"Plot":description})
	liz.setProperty('fanart_image', fanart)
	if mode==4:
		#liz.setProperty("IsPlayable","true")
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	elif mode==7 or mode==10 or mode==17:
		if getKodiVersion() > 19:
			info = liz.getVideoInfoTag()
			info.setTitle(name)
			info.setPlot(description)
		else:
			liz.setInfo( type="Video", infoLabels={"Title": name,"Plot":description})
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	else:
		if getKodiVersion() > 19:
			info = liz.getVideoInfoTag()
			info.setTitle(name)
			info.setPlot(description)
		else:
			liz.setInfo( type="Video", infoLabels={"Title": name,"Plot":description})
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok
	xbmcplugin.endOfDirectory
	
def addDirMeta(name,url,mode,iconimage,fanart,description,year,cast,rating,runtime,genre):
	u=sys.argv[0]+"?url="+urllib_parse.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib_parse.quote_plus(name)+"&iconimage="+urllib_parse.quote_plus(iconimage)+"&description="+urllib_parse.quote_plus(description)
	ok=True
	liz=xbmcgui.ListItem(name)
	liz.setArt({ 'thumb': iconimage, 'icon': iconimage, 'fanart': fanart})
	liz.setInfo( type="Video", infoLabels={"Title": name,"Plot":description,"Rating":rating,"Year":year,"Duration":runtime,"Cast":cast,"Genre":genre})
	liz.setProperty('fanart_image', fanart)
	liz.setProperty("IsPlayable","true")
	cm = []
	cm.append(('Play Trailer','XBMC.RunPlugin(plugin://plugin.video.flechanegra.vip/?mode=9&url='+str(name)+')'))
	cm.append(('Movie Information', 'XBMC.Action(Info)'))
	liz.addContextMenuItems(cm,replaceItems=True)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	return ok
	

def OPEN_URL(url):
	headers = {}
	headers['User-Agent'] = 'TheWizardIsHere'
	link = requests.session().get(url, headers=headers, verify=False).text
	return link


def clear_cache():
	xbmc.log('CLEAR CACHE ACTIVATED')
	xbmc_cache_path = os.path.join(control.transPath('special://home'), 'cache')
	confirm=xbmcgui.Dialog().yesno("Please Confirm","Please Confirm You Wish To Delete Your Kodi Application Data",nolabel="Cancel",yeslabel="Clear")
	if confirm:
		if os.path.exists(xbmc_cache_path)==True:
			for root, dirs, files in os.walk(xbmc_cache_path):
				file_count = 0
				file_count += len(files)
				if file_count > 0:


						for f in files:
							try:
								os.unlink(os.path.join(root, f))
							except:
								pass
						for d in dirs:
							try:
								shutil.rmtree(os.path.join(root, d))
							except:
								pass


		dialog = xbmcgui.Dialog()
		dialog.ok(ADDONTITLE, "Cache Cleared Successfully!")
		xbmc.executebuiltin("Container.Refresh()")
		
def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	return param
		
class Trailer:
    def __init__(self):
        self.base_link = 'http://www.youtube.com'
        self.key_link = 'QUl6YVN5QnZES3JnSU1NVmRPajZSb1pnUWhaSzRHM3MybDZXeVhn'
        self.key_link = '&key=%s' % base64.urlsafe_b64decode(self.key_link)
        self.search_link = 'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=5&q=%s'
        self.youtube_search = 'https://www.googleapis.com/youtube/v3/search?q='
        self.youtube_watch = 'http://www.youtube.com/watch?v=%s'

    def play(self, name, url=None):
        try:
            url = self.worker(name, url)
            if url == None: return

            title = control.infoLabel('listitem.title')
            if title == '': title = control.infoLabel('listitem.label')
            icon = control.infoLabel('listitem.icon')

            item = control.item(path=url, iconImage=icon, thumbnailImage=icon)
            try: item.setArt({'icon': icon})
            except: pass
            item.setInfo(type='Video', infoLabels = {'title': title})
            control.player.play(url, item)
        except:
            pass

    def worker(self, name, url):
        try:
            if url.startswith(self.base_link):
                url = self.resolve(url)
                if url == None: raise Exception()
                return url
            elif not url.startswith('http://'):
                url = self.youtube_watch % url
                url = self.resolve(url)
                if url == None: raise Exception()
                return url
            else:
                raise Exception()
        except:
            query = name + ' trailer'
            query = self.youtube_search + query
            url = self.search(query)
            if url == None: return
            return url


    def search(self, url):
        try:
            query = urllib_parse.parse_qs(urllib_parse.urlparse(url).query)['q'][0]

            url = self.search_link % urllib_parse.quote_plus(query) + self.key_link

            result = client.request(url)

            items = json.loads(result)['items']
            items = [(i['id']['videoId']) for i in items]

            for url in items:
                url = self.resolve(url)
                if not url is None: return url
        except:
            return


    def resolve(self, url):
        try:
            id = url.split('?v=')[-1].split('/')[-1].split('?')[0].split('&')[0]
            result = client.request('http://www.youtube.com/watch?v=%s' % id)

            message = client.parseDOM(result, 'div', attrs = {'id': 'unavailable-submessage'})
            message = ''.join(message)

            alert = client.parseDOM(result, 'div', attrs = {'id': 'watch7-notification-area'})

            if len(alert) > 0: raise Exception()
            if re.search('[a-zA-Z]', message): raise Exception()

            url = 'plugin://plugin.video.youtube/play/?video_id=%s' % id
            return url
        except:
            return
			
def MonthNumToName(num):
	if '01' in num:
		month = 'January'
	elif '02' in num:
		month = 'Febuary'
	elif '03' in num:
		month = 'March'
	elif '04' in num:
		month = 'April'
	elif '05' in num:
		month = 'May'
	elif '06' in num:
		month = 'June'
	elif '07' in num:
		month = 'July'
	elif '08' in num:
		month = 'Augast'
	elif '09' in num:
		month = 'September'
	elif '10' in num:
		month = 'October'
	elif '11' in num:
		month = 'November'
	elif '12' in num:
		month = 'December'
	return month