#!/usr/bin/python
#
# For Python 2.7
#
# Fish the last four MarketPlace shows, and some weekly shows
# off NPR onto my USB drive "DestDrive"
#
import urllib, os, sys, datetime, string
import sgmllib, htmllib, formatter, re

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
		self.hrefRE = re.compile( hrefRegex )
		htmllib.HTMLParser.__init__( self, formatter.NullFormatter() )

	def start_a( self, attrs ):
		d = dict(attrs)
		if (d.has_key('href') and self.hrefRE.search( d['href'] )):
			self.resultURL = d['href']
			self.urlList.append( d['href'] )

		# This grabs archived shows from the Serial prodcast.
		# the HREF above only gets the most recent in the page's
		# default player.
##		if (d.has_key('data-audio') and self.hrefRE.search( d['data-audio'])):
##			print "Archived episode: " + d['data-audio']

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

# Download the URL
def downloadNPRshow( mp3url, thumbPathStr, showName ):
	# Find last Saturday's date in Mmm_dd format
	lastSunStr = lastNday(5).strftime("%b_%d")
	ctFilePath = DestDrive + os.path.normpath(thumbPathStr % lastSunStr)
	if (os.path.exists( ctFilePath )):
		print "Already have %s for %s" % (showName, lastSunStr)
	elif (mp3url):
		ctShowMP3 = urllib.urlopen(mp3url).read()
		print "Getting %s for %s" % (showName, lastSunStr)
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

def getNPRShow( podCastID, thumbPathStr, showName ):
	podcastPage = urllib.urlopen( "http://www.npr.org/podcasts/%s" % podCastID ).read()
	g = re.search( "(http://[\w.]+/anon.npr-podcasts.*[.]mp3)", podcastPage )
	if (g):
		downloadNPRshow( g.group(1), thumbPathStr, showName )
	else:
		print "Link for %s MP3 not found in podcast page" % showName

# Use an HTML parser to fish the MP3s out of the NPR web site.
def processNPRShow( nprParser, urlstream, thumbPathStr, showName ):
	nprParser.feed( urlstream.read() )
	urlstream.close()
	downloadNPRshow( nprParser.resultURL, thumbPathStr, showName )

def getTAM( thumbPathStr ):
	nprParser = NPRshowParser( ".*[.]mp3$" )
	urlstream = urllib.urlopen( "http://thisamericanlife.org/" )
	processNPRShow( nprParser, urlstream, thumbPathStr, "This American Life" )

def getSerial( thumbPathStr ):
	nprParser = NPRshowParser( ".*serial-s\d\d-e\d\d[.]mp3$" )
	urlstream = urllib.urlopen( "http://serialpodcast.org/" )
	processNPRShow( nprParser, urlstream, thumbPathStr, "Serial Podcast" )

def getFreak( thumbPathStr ):
	# Can pass the date at some point in the future.
	# MP3 URL ends with ".../freakonomics_podcastMMDDYY.mp3"
	# For now grab the first in the file (most recent)
	nprParser = NPRshowParser( ".*[.]mp3$" )
	urlstream = urllib.urlopen( "http://feeds.feedburner.com/freakonomicsradio" )
	processNPRShow( nprParser, urlstream, thumbPathStr, "Freakanomics Radio" )

def getTAMepisode( showNumber ):
	print "# Downloading TAM episode #%s" % showNumber
	tamURL = "http://audio.thisamericanlife.org/jomamashouse/ismymamashouse/%s.mp3"
	mp3data = urllib.urlopen( tamURL % showNumber ).read()
	file( DestDrive + os.sep + "TAM"+ os.sep + "TAM_%s.mp3" % showNumber, 'wb' ).write( mp3data )

def getPlanetMoney( lastCount, thumbPath ):

	def moneyDownload( moneyURLs, moneyDay ):
		# Search the list of Planet Money URLs for the show w/desired date
		searchKey = re.compile(moneyDay.strftime( "%Y/%m/%Y%m%d"))
		moneyURL = None
		for url in moneyURLs:
			if searchKey.search( url ):
				moneyURL = url
				break

		if not moneyURL:
			print "Can't find Planet Money for %s" % moneyDay.strftime("%b %d")
			return False

		moneyMP3=urllib.urlopen( moneyURL )
		if (moneyMP3.getcode() == 200):
			print "Getting Planet Money for %s" % moneyDay.strftime("%b %d")
			file( DestDrive + os.path.normpath( thumbPath % (moneyDay.strftime("%b_%d"))), 'wb').write( moneyMP3.read() )
			return True
		else:
			print "Error %d loading %s" % (moneyMP3.getcode(), moneyURL)
			return False

	# Rather than try and guess the URLs, we look for Planet Money shows
	# by date instead.

	nprParser = NPRshowParser( ".*[.]mp3[?]dl=1$" )
	urlstream = urllib.urlopen( "http://www.npr.org/blogs/money/")
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

	[os.remove(f) for f in os.listdir(DestFolder)]

	weekendOffset = 0
	for i in range(0, numDaysToGet):
		d = datetime.date.today() - datetime.timedelta(i)
		# Skip weekends (6 == sunday)
		if (d.weekday() == 6):
			weekendOffset += 2
		d = d - datetime.timedelta(weekendOffset) # Skip weekends
		print d.strftime("Getting Marketplace for %b %d, %Y...")
		showurl = genurl(d)
		showMP3 = urllib.urlopen(showurl).read()
		file( DestFolder + "MKT_%02d.mp3" % d.day, 'wb' ).write(showMP3)

	os.chdir(os.path.normpath("/"))    # So USB key isn't locked.

def clean():
	folders = ["ATC", "CARTALK", "FAIR", "FNR", "MKTPLC", "INVIS", "SCIFRI", "TAM", "TED", "WW"]
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
	getNPRShow( "510208", '/CARTALK/CT_%s.mp3', "Car Talk" )
	getNPRShow( "344098539", '/WW/WW_%s.mp3', "Wait Wait" )
	getNPRShow( "510307", '/INVIS/Invis_%s.mp3', "Invisibilia" )
	getTAM( '/TAM/TAM_%s.mp3' )
##	getSerial( '/TAM/Serial_%s.mp3' )
	getMarketPlace()
	getFreak( '/FNR/FNR_%s.mp3' )
	getPlanetMoney( 1, "/ATC/Money_%s.mp3" )
	getPlanetMoney( 2, "/ATC/Money_%s.mp3" )
	getPlanetMoney( 3, "/ATC/Money_%s.mp3" )
	getPlanetMoney( 4, "/ATC/Money_%s.mp3" )

def main():
	if (len(sys.argv) > 1 and sys.argv[1] == "clean"):
		clean()
	elif (len(sys.argv) > 2 and sys.argv[1] == "tam"):
		getTAMepisode( sys.argv[2] )
	else:
		getNPRShows()

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
