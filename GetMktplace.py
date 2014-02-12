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
		self.hrefRE = re.compile( hrefRegex )
		htmllib.HTMLParser.__init__( self, formatter.NullFormatter() )

	def start_a( self, attrs ):
		d = dict(attrs)
		if (self.hrefRE.search( d['href'] )):
			self.resultURL = d['href']

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

# Use an HTML parser to fish the MP3s out of the NPR web site.
def processNPRShow( nprParser, urlstream, thumbPathStr, showName ):
	nprParser.feed( urlstream.read() )
	urlstream.close()

	# Find last Saturday's date in Mmm_dd format
	lastSunStr = lastNday(5).strftime("%b_%d")
	ctFilePath = DestDrive + os.path.normpath(thumbPathStr % lastSunStr)
	if (os.path.exists( ctFilePath )):
		print "Already have %s for %s" % (showName, lastSunStr)
	elif (nprParser.resultURL):
		ctShowMP3 = urllib.urlopen(nprParser.resultURL).read()
		print "Getting %s for %s" % (showName, lastSunStr)
		file( ctFilePath, 'wb' ).write( ctShowMP3 )
	else:
		print "Unable to get %s for %s" % (showName, lastSunStr)

# Download a weekly NPR show.
# The podcasts are stored at a link like this (e.g., CarTalk):
#  http://www.npr.org/rss/podcast/podcast_detail.php?siteId=9911203
# where the number changes by show.  On that page, you look for a link like this:
#  http://public.npr.org/anon.npr-podcasts/podcast/510208/145572190/npr_145572190.mp3?dl=1
# with the MP3 file.

def getNPRShow( podCastID, thumbPathStr, showName ):
	nprParser = NPRshowParser( ".*npr-podcasts.*" )
	urlstream = urllib.urlopen( "http://www.npr.org/rss/podcast/podcast_detail.php?siteId=%s" % podCastID )
	processNPRShow( nprParser, urlstream, thumbPathStr, showName )

def getTAM( thumbPathStr ):
	nprParser = NPRshowParser( ".*[.]mp3$" )
	urlstream = urllib.urlopen( "http://thisamericanlife.org/" )
	processNPRShow( nprParser, urlstream, thumbPathStr, "This American Life" )

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
	def moneyDownload( moneyDay, key ):
		moneyURL=moneyDay.strftime("http://pd.npr.org/anon.npr-mp3/npr/blog/%Y/%m/%Y%m%d_blog_" + key + ".mp3?dl=1")
		print "Getting Planet Money (%s) for " % key + moneyDay.strftime("%b %d")
		moneyMP3=urllib.urlopen( moneyURL )
		if (moneyMP3.getcode() == 200):
			file( DestDrive + os.path.normpath( thumbPath % (moneyDay.strftime("%b_%d"))), 'wb').write( moneyMP3.read() )
			return True
		else:
			print "Error %d loading %s" % (moneyMP3.getcode(), moneyURL)
			return False

	# Sample URL
	# http://pd.npr.org/anon.npr-mp3/npr/blog/2013/10/20131004_blog_pmoney.mp3?dl=1
	# Note the Planet Money guys get sloppy.  Sometimes the date in the filename portion
	# of the string is off, sometimes they use "pmpod" instead of "pmoney".
	
	if (not moneyDownload( lastNday( lastCount ), "pmoney" )):
		print "Trying pmpod download..."
		moneyDownload( lastNday( lastCount ), "pmpod" )
		

# Get the last four (numDaysToGet) episodes of Marketplace.  The MP3
# location is computed directly from the date.
def getMarketPlace():
	def genurl(d):
		urlStr="http://download.publicradio.org/podcast/marketplace/pm/%4d/%02d/%02d/marketplace_podcast_%4d%02d%02d_64.mp3"
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
	folders = ["ATC", "CARTALK", "FAIR", "FNR", "MKTPLC", "SCIFRI", "TAM", "TED", "WW"]
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
	getNPRShow( "9911203", '/CARTALK/CT_%s.mp3', "Car Talk" )
	getNPRShow( "5183214", '/WW/WW_%s.mp3', "Wait Wait" )
	getTAM( '/TAM/TAM_%s.mp3' )
	getMarketPlace()
	getFreak( '/FNR/FNR_%s.mp3' )
	getPlanetMoney( 2, "/ATC/Money_%s.mp3" )
	getPlanetMoney( 4, "/ATC/Money_%s.mp3" )

if (len(sys.argv) > 1 and sys.argv[1] == "clean"):
	clean()
elif (len(sys.argv) > 2 and sys.argv[1] == "tam"):
    getTAMepisode( sys.argv[2] )
else:
	getNPRShows()

# Note back issues of TAM are found here:
# http://audio.thisamericanlife.org/jomamashouse/ismymamashouse/SHOWNUMBER.mp3

# This link has segment-by-segment breakdowns of Science Friday
# http://www.sciencefriday.com/audio/scifriaudio.xml

# Freakanomics Radio:
# http://feeds.feedburner.com/freakonomicsradio

# Planet Money podcasts look like this:
#  http://pd.npr.org/anon.npr-mp3/npr/blog/2013/10/20131009_blog_pmoney.mp3?dl=1
#  http://pd.npr.org/anon.npr-mp3/npr/blog/2013/10/20131004_blog_pmoney.mp3?dl=1
#  http://pd.npr.org/anon.npr-mp3/npr/blog/2013/10/20131002_blog_pmoney.mp3?dl=1
#  http://pd.npr.org/anon.npr-mp3/npr/blog/2013/09/20130927_blog_pmpod.mp3?dl=1
#  http://pd.npr.org/anon.npr-mp3/npr/blog/2013/09/20130925_blog_pmoney.mp3?dl=1
# http://pd.npr.org/anon.npr-mp3/npr/blog/2013/10/20131025_blog_pmoney.mp3?dl=1
# So you need to grab most recent Wed & Fri.
