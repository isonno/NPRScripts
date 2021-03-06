#!/usr/bin/python
#
# THIS CODE IS DEPRECATED. Use PodcastWeek.py instead.
#
# For Python 2.7
#
# Fish the last four MarketPlace shows, and some weekly shows
# off NPR onto my USB drive "DestDrive"
#
import urllib2, os, sys, datetime, string, glob
import sgmllib, htmllib, formatter, re, subprocess

def getWindowsDrives():		# http://stackoverflow.com/questions/827371
	from ctypes import windll
	drives = []
	bitmask = windll.kernel32.GetLogicalDrives()
	for letter in string.uppercase:
		if bitmask & 1:
			drives.append(letter + ":")
		bitmask >>= 1

	return drives

DestDrive = None

def setDestinationDrive():
	global DestDrive
	if sys.platform == "darwin":
		DestDrive = "/Volumes/AUDIO"
	else:
		winDrives = getWindowsDrives()[1:]	# Skip the C: drive
		for d in winDrives:
			if (os.path.exists( d + os.path.sep + "MKTPLC" )):
				DestDrive = d
				break
		if (not DestDrive):
			print "NPR Thumb drive missing?  It must have a MKTPLC folder"
			sys.exit(-1)

# Walk through a web site, collecting anchors matching "hrefRegex"

class NPRshowParser( htmllib.HTMLParser ):
	def __init__(self, hrefRegex):
		self.resultURL = None
		self.urlList = []
		self.anchorClass = None
		self.hrefRE = re.compile( hrefRegex )
		htmllib.HTMLParser.__init__( self, formatter.NullFormatter() )

	def start_a( self, attrs ):
		d = dict(attrs)
		if (self.anchorClass):
			if not d.has_key('class') or d['class'] != self.anchorClass:
				return
		if (d.has_key('href') and self.hrefRE.search( d['href'] )):
			if (not self.resultURL):
				self.resultURL = d['href']
			self.urlList.append( d['href'] )

		# This grabs archived shows from the Serial prodcast.
		# the HREF above only gets the most recent in the page's
		# default player.
##		if (d.has_key('data-audio') and self.hrefRE.search( d['data-audio'])):
##			print "Archived episode: " + d['data-audio']

	# The new podcast site uses <div ... data-html5-url="..."  >
	def start_div( self, attrs ):
		d = dict(attrs)
		urlkey = 'data-html5-url'
		if (d.has_key(urlkey) and self.hrefRE.search( d[urlkey] )):
			self.urlList.append( d[urlkey] )
			self.resultURL = self.urlList[0]

	# Freakanomics uses an XML file
	def start_enclosure( self, attrs ):
		# for Freakanomics
		# only grab the first one for now; later can search for date
		d = dict(attrs)
		if not self.resultURL and (self.hrefRE.search( d['url'] )):
			self.resultURL = d['url']

# Return the date of the last specified weekday (0=Mon, 1=Tue...6=Sun)
def lastNday(n):
	return (datetime.date.today() - datetime.timedelta( datetime.date.today().weekday()+(7-n)%7 ))

def mp3FileExists(path):
	return os.path.exists(path) and (os.path.getsize(path) > 0)

# Download the URL
def downloadNPRshow( mp3url, thumbPathStr, showName ):
	# Find last Saturday's date in Mmm_dd format
	g = re.search("/([\w_.]+[.]mp3)$", mp3url)
	mp3filename = " (filename: %s)" % g.group(1) if g else ""
	lastSunStr = lastNday(5).strftime("%b_%d")
	ctFilePath = DestDrive + os.path.normpath(thumbPathStr % lastSunStr)
	if (mp3FileExists( ctFilePath )):
		print "Already have %s for %s" % (showName, lastSunStr)
	elif (mp3url):
		ctShowMP3 = urllib2.urlopen(mp3url).read()
		print "Getting %s for %s" % (showName, lastSunStr) + mp3filename
		file( ctFilePath, 'wb' ).write( ctShowMP3 )
	else:
		print "Unable to get %s for %s" % (showName, lastSunStr)

# Download a weekly NPR show.
# The podcast home pages are stored at URLs like (e.g., CarTalk):
#  http://www.npr.org/podcasts/510208 [/car_talk]
# where the number changes by show.  On that page, you look for a link like this:
#  http://public.npr.org/anon.npr-podcasts/podcast/510208/145572190/npr_145572190.mp3?dl=1
# with the MP3 file suffix.
# NOTE:
# As of Jan '15, the link is now buried in JavaScript,
# so you can't use the HTML parser any more.
# So we just search the raw HTML stream (incl the JavaScript) now.
# This version does that, but see below...

##def getNPRShow1( podCastID, thumbPathStr, showName ):
##	podcastPage = urllib2.urlopen( "http://www.npr.org/podcasts/%s" % podCastID ).read()
##	g = re.search( "(http://[\w.]+/anon.npr-podcasts[\w/-]*[.]mp3)", podcastPage )
##	if (g):
##		downloadNPRshow( g.group(1), thumbPathStr, showName )
##	else:
##		print "Link for %s MP3 not found in podcast page" % showName

# Use an HTML parser to fish the MP3s out of the NPR web site.
def processNPRShow( nprParser, urlstream, thumbPathStr, showName ):
	nprParser.feed( urlstream.read() )
	urlstream.close()
	downloadNPRshow( nprParser.resultURL, thumbPathStr, showName )

# Serial started using a CDN that's snotty about non-browser clients
# See http://www.diveintopython.net/http_web_services/user_agent.html
def urlOpenWithAgent(theurl):
    uaStr = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
    request = urllib2.Request(theurl)
    request.add_header('User-Agent', uaStr )
    opener = urllib2.build_opener()
    return opener.open(request)

# Well, actually, it turns out the .mp3 links are also buried in <DIV> tags.
#  <div class="audio-player"
#    data-id="381440789"
#    data-html5-url="http://podcastdownload.npr.org/anon.npr-podcasts/podcast/344098539/377296249/npr_377296249.mp3"
#    [...] >
# So we can fix the NPR parser to look for these DIV parameters.

def getNPRShow( podCastID, thumbPathStr, showName ):
	nprParser = NPRshowParser( "http.*[.]mp3" )
#	nprParser.anchorClass = 'audio-module-listen'
	urlstream = urlOpenWithAgent( "http://www.npr.org/podcasts/%s" % podCastID )
	processNPRShow( nprParser, urlstream, thumbPathStr, showName )

def getTAM( thumbPathStr ):
	nprParser = NPRshowParser( "http.*[.]mp3$" )
	urlstream = urlOpenWithAgent( "http://thisamericanlife.org/" )
#	processNPRShow( nprParser, urlstream, thumbPathStr, "This American Life" )
	nprParser.feed( urlstream.read() )
	urlstream.close()
	if len(nprParser.urlList) == 0:
		print "# ERROR - .mp3 download link missing on TAM home page??"
	else:
		print nprParser.urlList[-1]
		downloadNPRshow( nprParser.urlList[-1], thumbPathStr, "This American Life" )

def getSerial( thumbPathStr ):
	nprParser = NPRshowParser( "http.*serial-s\d\d-e\d\d[.]mp3$" )
	urlstream = urlOpenWithAgent( "https://serialpodcast.org/" )
	processNPRShow( nprParser, urlstream, thumbPathStr, "Serial Podcast" )

def getFreak( thumbPathStr ):
	# Can pass the date at some point in the future.
	# MP3 URL ends with ".../freakonomics_podcastMMDDYY.mp3"
	# For now grab the first in the file (most recent)
	nprParser = NPRshowParser( "http.*[.]mp3$" )
	urlstream = urllib2.urlopen( "http://feeds.feedburner.com/freakonomicsradio" )
	processNPRShow( nprParser, urlstream, thumbPathStr, "Freakanomics Radio" )

def getTAMepisode( showNumber ):
	print "# Downloading TAM episode #%s" % showNumber
	tamURL = "http://audio.thisamericanlife.org/jomamashouse/ismymamashouse/%s.mp3"
	mp3data = urllib2.urlopen( tamURL % showNumber ).read()
	file( DestDrive + os.sep + "TAM"+ os.sep + "TAM_%s.mp3" % showNumber, 'wb' ).write( mp3data )

#
# Planet money & Marketplace happen multiple times a week,
# so muck with them differently
#
def getPlanetMoney( lastCount, thumbPath ):
	def moneyDownload( moneyURLs, moneyDay ):
		# Search the list of Planet Money URLs for the show w/desired date
		searchKey = re.compile(moneyDay.strftime( "%Y/%m/%Y%m%d"))
		moneyURL = None
		moneyPath = DestDrive + os.path.normpath( thumbPath % (moneyDay.strftime("%b_%d")))
		for url in moneyURLs:
			if searchKey.search( url ):
				moneyURL = url
				break

		moneyDateStr = moneyDay.strftime("%b %d")

		if not moneyURL:
			print "Can't find Planet Money for %s" % moneyDateStr
			return False

		if (mp3FileExists(moneyPath)):
			print "Already have Planet Money for %s" % moneyDateStr
			return True

		moneyMP3=urllib2.urlopen( moneyURL )
		if (moneyMP3.getcode() == 200):
			print "Getting Planet Money for %s" % moneyDateStr
			file( moneyPath, 'wb').write( moneyMP3.read() )
			return True
		else:
			print "Error %d loading %s" % (moneyMP3.getcode(), moneyURL)
			return False

	# Rather than try and guess the URLs, we look for Planet Money shows
	# by date instead.

	nprParser = NPRshowParser( ".*[.]mp3.*[&]dl=1$" )
	urlstream = urllib2.urlopen( "http://www.npr.org/podcasts/510289/planet-money/")
	nprParser.feed( urlstream.read() )
	urlstream.close()

	moneyDownload( nprParser.urlList, lastNday( lastCount ) )

# Get the last four (numDaysToGet) episodes of Marketplace.  The MP3
# location is computed directly from the date.
def getMarketPlace():
	def genurl(d):
		urlStr="http://www.podtrac.com/pts/redirect.mp3/download.publicradio.org/podcast/marketplace/pm/%4d/%02d/%02d/pm_%4d%02d%02d_pod_64.mp3"
		return urlStr % (d.year, d.month, d.day, d.year, d.month, d.day )

	DestFolder = DestDrive + os.path.normpath("/MKTPLC") + os.path.sep
	numDaysToGet = 4

	os.chdir(DestFolder)

	weekendOffset = 0
	for i in range(0, numDaysToGet):
		d = datetime.date.today() - datetime.timedelta(i)
		# Skip weekends (6 == sunday)
		if (d.weekday() == 6):
			weekendOffset += 2
		d = d - datetime.timedelta(weekendOffset) # Skip weekends
		mktPath = DestFolder + "MKT_%02d.mp3" % d.day
		if mp3FileExists(mktPath):
			print d.strftime("Already have Marketplace for %b %d, %Y...")
		else:
			print d.strftime("Getting Marketplace for %b %d, %Y...")
			showurl = genurl(d)
			try:
				showStream = urllib2.urlopen(showurl)
				showMP3 = showStream.read()
				file( mktPath, 'wb' ).write(showMP3)
			except:
				print d.strftime("Marketplace for %b %d, %Y is not available")

	os.chdir(os.path.normpath("/"))    # So USB key isn't locked.

def clean():
	folders = ["99PI", "ATC", "CARTALK", "FAIR", "FNR", "MKTPLC", "INVIS", "HT", "GIM", "SCIFRI", "TAM", "TED", "WW"]
	for fold in folders:
		path = DestDrive + os.path.sep + fold + os.path.sep
		if not os.path.exists( path ):
			print "Creating folder %s..." % path
			os.mkdir( path )
		else:
			print "Cleaning %s..." % path
			[os.remove(path + f) for f in os.listdir( path )]

# Weekly shows
def getNPRShows():
##	getNPRShow( "510208", '/CARTALK/CT_%s.mp3', "Car Talk" )  # Tom Magliozzi, RIP
	getNPRShow( "344098539", '/WW/WW_%s.mp3', "Wait Wait" )
	getNPRShow( "510307", '/INVIS/Invis_%s.mp3', "Invisibilia" )  # Season ended
##	getSerial( '/TAM/Serial_%s.mp3' )        # Season 2 ended
##	getNPRShow( "510303", '/HT/HowTo_%s.mp3', "How To" )	# Boring
	getTAM( '/TAM/TAM_%s.mp3' )
	getMarketPlace()
	getFreak( '/FNR/FNR_%s.mp3' )
	for i in range(1,5):
		getPlanetMoney( i, "/ATC/Money_%s.mp3" )

# The MP3 Player on my '11 Honda Insight gags on some of
# the podcast MP3 files NPR distributes.  Re-encoding
# them with ffmpeg works around the problem.
def reEncodeShow(show):
	path = DestDrive + os.sep + show + os.sep
	files = glob.glob(path + "*.mp3")
	try:
		for f in files:
			print "Re-encoding %s..." % f
			subprocess.call(["ffmpeg", "-i", f, "-ac", "2", path+"tmp.mp3"])
			os.remove(f)
			os.rename(path+"tmp.mp3", f)
	except OSError:
		print "Unable to run ffmpeg"

def main():
	setDestinationDrive()
	if (len(sys.argv) > 1 and sys.argv[1] == "clean"):
		clean()
	elif (len(sys.argv) > 2 and sys.argv[1] == "tam"):
		getTAMepisode( sys.argv[2] )
	else:
		getNPRShows()
##		reEncodeShow("WW")
##		reEncodeShow("HT")

main()

# Note back issues of TAM are found here:
# http://audio.thisamericanlife.org/jomamashouse/ismymamashouse/SHOWNUMBER.mp3

# This link has segment-by-segment breakdowns of Science Friday
# http://www.sciencefriday.com/audio/scifriaudio.xml

# Freakanomics Radio:
# http://feeds.feedburner.com/freakonomicsradio

# Serial Podcast
# http://dts.podtrac.com/redirect.mp3/files.serialpodcast.org/sites/default/files/podcast/1417670735/serial-s01-e10.mp3 (current)
# http://dts.podtrac.com/redirect.mp3/files.serialpodcast.org/sites/default/files/podcast/serial-s01-e01_0.mp3 (past)
# http://dts.podtrac.com/redirect.mp3/files.serialpodcast.org/sites/default/files/podcast/serial-s01-e02.mp3
# ...
# http://dts.podtrac.com/redirect.mp3/files.serialpodcast.org/sites/default/files/podcast/serial-s01-e05.mp3
# Magic number delta e06 to e07 is 599,877. The seconds in a week is 604,800 so it's a posting timestamp
# http://dts.podtrac.com/redirect.mp3/files.serialpodcast.org/sites/default/files/podcast/1414645971/serial-s01-e06.mp3
# ...
# http://dts.podtrac.com/redirect.mp3/files.serialpodcast.org/sites/default/files/podcast/1417670735/serial-s01-e12.mp3

# Planet Money podcasts look like this:
#  http://pd.npr.org/anon.npr-mp3/npr/blog/2013/10/20131009_blog_pmoney.mp3?dl=1
#  http://pd.npr.org/anon.npr-mp3/npr/blog/2013/10/20131004_blog_pmoney.mp3?dl=1
#  http://pd.npr.org/anon.npr-mp3/npr/blog/2013/10/20131002_blog_pmoney.mp3?dl=1
#  http://pd.npr.org/anon.npr-mp3/npr/blog/2013/09/20130927_blog_pmpod.mp3?dl=1
#  http://pd.npr.org/anon.npr-mp3/npr/blog/2013/09/20130925_blog_pmoney.mp3?dl=1
# http://pd.npr.org/anon.npr-mp3/npr/blog/2013/10/20131025_blog_pmoney.mp3?dl=1
# So you need to grab most recent Wed & Fri.
