#!/usr/bin/python
# -*- coding: utf-8 -*-
__addonname__     = "Audio Bible Browser"
__addonid__       = "plugin.audio.audiobible"
__author__        = "clcii"

import urllib,urllib2,re,sys,base64,socket,time #,pickle,collections
from xbmcswift2 import Plugin,xbmc,xbmcgui,ListItem,actions
from datetime import date
#from itertools import izip
import bibledata


socket.setdefaulttimeout(30)
plugin = Plugin('plugin.audio.audiobible')
forceViewMode=plugin.get_setting("forceViewMode", unicode)
viewMode=plugin.get_setting("viewMode", unicode)
basegatewayurl="http://www.biblegateway.com/audio/"

@plugin.route('/')
def enMain():
	items = [
		{'label': 'My Audio Bible', 'path': plugin.url_for('listMyBible')},
		{'label': 'Wisdom and Songs of the Day', 'path': plugin.url_for('listWisdomAndSongs')},
		{'label': 'Audio Bible Browser', 'path': plugin.url_for('listRecordings')}
	]
	recording=plugin.get_setting("defaultrecording", unicode)
	if forceViewMode=="true":
		xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
	return plugin.finish(items)
@plugin.route('/listMyBible/')
def listMyBible():
	defaultrecording=plugin.get_setting("defaultrecording",unicode)
	plugin.redirect('plugin://plugin.audio.audiobible/Browser/'+defaultrecording+'/')
@plugin.route('/Browser/')
def listRecordings():
	recordings=[]
	defaultrecording=str(plugin.get_setting("defaultrecording", unicode))
	alllanguages = sorted(bibledata.languagelib)
	for language in alllanguages:
		thislanguage = bibledata.languagelib[language]
		recordings.append({'label': thislanguage['title'], 
                            'path': plugin.url_for('listRecordings'),
                            'icon': 'DefaultShortcut.png'})
		for index in bibledata.recordinglib:
			recording = dict(bibledata.recordinglib[index])
			if recording['language']==language:
				alabel = recording['title']
				if recording['code']==defaultrecording:
					alabel=alabel + " (Current Default Recording)"
				recordings.append(
				{'label': alabel, 
				'path': plugin.url_for('listBooks', recording=recording['code']),
				'context_menu':[
					makedefaultrecording(recording['code'])
				],
				'icon': 'DefaultArtist.png'
				}
				)
		if forceViewMode=="true":
			xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
	return plugin.finish(recordings)
@plugin.route('/Browser/<recording>/')
def listBooks(recording):
	thisrecording = bibledata.recordinglib[recording]
	print(recording)
	books=[]
	allBooks=bibledata.booklib
	codes = dict(bibledata.bookorderlib)
	#for code, title in match:
	for item in codes:
 		code=codes[item]
 		book=dict(allBooks[code])
 		title=book['title']
		#or (bibledata.pluswisdom[recording] <> '' and (code=='Prov' or code=='Ps'))
 		if book['section']==thisrecording['section'] or thisrecording['section']=='ALL' or (thisrecording['pluswisdom'] == 1 and (code=='Prov' or code=='Ps')):
 			books.append(
 			{'label': title, 
 			'path': plugin.url_for('listChapters',recording=recording, book=code), 
 		 	'icon': 'DefaultPlaylist.png'}
 			)
	if forceViewMode=="true":
		xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
	return plugin.finish(books)
@plugin.route('/Browser/<recording>/<book>')
def listChapters(recording, book):
	thisrecording = bibledata.recordinglib[recording]
	thisbook=bibledata.booklib[book]
	chapters=thisbook['chapters']
	booktitle=thisbook['title']
	chapterslist=[]
	for x in range(1, chapters+1):
			title=booktitle +" - Chapter "+ str(x)
			chaptercode=book +"."+str(x)
			chapterslist.append(
				{'label': title, 
				'path': plugin.url_for('playChapter', 
				recording=recording, 
				book=book, 
				chapter=chaptercode),
				'icon': 'DefaultAudio.png',
				'info': ('audio'),
				'is_playable': True
				}
				)
	return plugin.finish(chapterslist)
@plugin.route('/listWisdomAndSongs/')
def listWisdomAndSongs():
	recording=plugin.get_setting("defaultrecording", unicode)
	thisrecording = bibledata.recordinglib[recording]
	chapterslist=[]	
	if thisrecording['section']=='NT' and thisrecording['pluswisdom']==0:
		chapterslist.append(
		{'label': 'Psalms and Proverbs not available with this default recording.', 
		'path': plugin.url_for('listMyBible'), 
		'icon': 'DefaultAudio.png',
		'info': ('audio'),
		'is_playable': False
		})
	else:
		today=date.today()
		thisday=today.day

		#Add Proverbs
		book='Prov'
		title='Proverbs '+ str(thisday)
		chaptercode=book+'.'+str(thisday)
		chapterslist.append(
				{'label': title, 
				'path': plugin.url_for('playChapter', 
				recording=recording, 
				book=book, 
				chapter=chaptercode),
				'icon': 'DefaultAudio.png',
				'info': ('audio'),
				'is_playable': True
				}
				)
	#Add Psalms
		if thisday==31:
			book='Ps'
			psalm=str(119)
			title='Psalms '+ psalm
			chaptercode=book+'.'+psalm
			chapterslist.append(
			{'label': title, 
			'path': plugin.url_for('playChapter', 
			recording=recording, 
			book=book, 
			chapter=chaptercode),
			'icon': 'DefaultAudio.png',
			'info': ('audio'),
			'is_playable': True
			}
				)
		else:
			for x in range(1, 6):
				book='Ps'
				psalm=str((thisday*5) - (5-x))
				title='Psalms '+ psalm
				chaptercode=book+'.'+psalm
				chapterslist.append(
								{'label': title, 
								'path': plugin.url_for('playChapter', 
													recording=recording, 
													book=book, 
													chapter=chaptercode),
								'icon': 'DefaultAudio.png',
								'info': ('audio'),
								'is_playable': True
								}
								)
	return plugin.finish(chapterslist)
@plugin.route('/Play/<recording>/<book>/<chapter>')
def playChapter(recording, book, chapter):
	try:
		chapter_url=basegatewayurl+getrecordingpath(recording)+chapter
		mp3path=getMp3link(chapter_url)
		bookinfo=bibledata.booklib[book]
		title=bookinfo['title'] + ' ' + chapter[:chapter.find('.')]
		extinfo={'title':title,'album':recording}
		listitem={'label': title,
				'path':mp3path,
				'icon':'DefaultAudio.png',
				'info_type':'audio',
				'info':extinfo,
				'is_playable': True
		}  
		return plugin.set_resolved_url(listitem)
	except ValueError:
		dialog = xbmcgui.Dialog()
		dialog.ok("Unable to play recording")
		xbmc.PlayerControl(Stop)
		
@plugin.route('/setdefaultrecording/<code>')
def setdefaultrecording(code):
	plugin.set_setting('defaultrecording',code)
	plugin.log.debug('current default'+code)
	plugin.redirect('plugin://plugin.audio.audiobible/')
	xbmc.executebuiltin('Container.Refresh()')
#functions	
def makedefaultrecording(code):
	label = 'Set Default Recording'
	new_url = plugin.url_for('setdefaultrecording', code=code)
	return(label, actions.background(new_url))

def parameters_string_to_dict(parameters):
        ''' Convert parameters encoded in a URL to a dict. '''
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def getUrl(url):
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:18.0) Gecko/20100101 Firefox/18.0')
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		return link
	except ValueError:
		dialog.xbmcgui.Dialog()
		dialog.ok('Error','Unable to complete request')

def getMp3link(url):
	content = getUrl(url)
	content = content[content.find('<audio id="audio-player" autoplay="autoplay">'):]
	content = content[content.find('<source src="')+13:]
	content = content[content.find(''):]
	content = content[:content.find('">')]
	mp3path = content
	return mp3path
def getrecordingpath(url):
	reader=url[url.find("-")+1:]
	style=url[:url.find("-")]
	path = reader + "/" + style + "/"
	return(path)
if __name__=='__main__':
	try:
		import StorageServer
	except:
		import storageserverdummy as StorageServer
	cache = StorageServer.StorageServer('AudioBible',24)
	try:
		plugin.run()
	except IOError:
		plugin.notify('Network Error')