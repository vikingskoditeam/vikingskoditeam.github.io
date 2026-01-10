import sys
import xbmcgui
import xbmcplugin

addon_handle = int(sys.argv[1])

xbmcplugin.setContent(addon_handle, 'audio')

url = 'http://player.stmsg.com.br/player/6952/realplayer.rm'
li = xbmcgui.ListItem('Estudio KAZA FM - Servidor 1')
li.setInfo('music', { 'genre': 'Webradio' })
li.setIconImage('special://home/addons/plugin.audio.estudioKaza/resources/icon.png')
li.setArt({'thumb': "special://home/addons/plugin.audio.estudioKaza/resources/icon.png", 'fanart': 'special://home/addons/plugin.audio.estudioKaza/resources/fanart.jpg'})
xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)


url = 'http://player.stmsg.com.br/player/6952/winamp.pls'
li = xbmcgui.ListItem('Estudio KAZA FM - Servidor 2')
li.setInfo('music', { 'genre': 'Webradio' })
li.setIconImage('special://home/addons/plugin.audio.estudioKaza/resources/icon.png')
li.setArt({'thumb': "special://home/addons/plugin.audio.estudioKaza/resources/icon.png", 'fanart': 'special://home/addons/plugin.audio.estudioKaza/resources/fanart.jpg'})
xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

url = 'http://player.stmsg.com.br/player/6952/mediaplayer.asx'
li = xbmcgui.ListItem('Estudio KAZA FM - Servidor 3')
li.setInfo('music', { 'genre': 'Webradio' })
li.setIconImage('special://home/addons/plugin.audio.estudioKaza/resources/icon.png')
li.setArt({'thumb': "special://home/addons/plugin.audio.estudioKaza/resources/icon.png", 'fanart': 'special://home/addons/plugin.audio.estudioKaza/resources/fanart.jpg'})
xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
xbmcplugin.endOfDirectory(addon_handle)