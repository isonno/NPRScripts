#
# Fish the last four MarketPlace shows, and some weekly shows
# off NPR onto my USB drive "E:"
#
import urllib, os, sys, datetime
import sgmllib, htmllib, formatter, re

DestDrive = "G:"

# Download a weekly NPR show.
# The podcasts are stored at a link like this (e.g., CarTalk):
#  http://www.npr.org/rss/podcast/podcast_detail.php?siteId=9911203
# where the number changes by show.  On that page, you look for a link like this:
#  http://public.npr.org/anon.npr-podcasts/podcast/510208/145572190/npr_145572190.mp3?dl=1
# with the MP3 file.

class NPRshowParser( htmllib.HTMLParser ):
	def __init__(self, hrefRegex):
		self.resultURL = None
		self.hrefRE = re.compile( hrefRegex )
		htmllib.HTMLParser.__init__( self, formatter.NullFormatter() )

	def start_a( self, attrs ):
		d = dict(attrs)
		if (self.hrefRE.search( d['href'] )):
			self.resultURL = d['href']

def processNPRShow( nprParser, urlstream, thumbPathStr, showName ):
	nprParser.feed( urlstream.read() )
	urlstream.close()

	# Find last Sunday's date in Mmm_dd format
	lastSunStr = (datetime.date.today() - datetime.timedelta( datetime.date.today().weekday()+2 )).strftime("%b_%d")
	ctFilePath = DestDrive + thumbPathStr % lastSunStr
	if (os.path.exists( ctFilePath )):
		print "Already have %s for %s" % (showName, lastSunStr)
	elif (nprParser.resultURL):
		ctShowMP3 = urllib.urlopen(nprParser.resultURL).read()
		print "Getting %s for %s" % (showName, lastSunStr)
		file( ctFilePath, 'wb' ).write( ctShowMP3 )
	else:
		print "Unable to get %s for %s" % (showName, lastSunStr)

def getNPRShow( podCastID, thumbPathStr, showName ):
	nprParser = NPRshowParser( ".*npr-podcasts.*" )
	urlstream = urllib.urlopen( "http://www.npr.org/rss/podcast/podcast_detail.php?siteId=%s" % podCastID )
	processNPRShow( nprParser, urlstream, thumbPathStr, showName )

def getTAM( thumbPathStr ):
	nprParser = NPRshowParser( ".*[.]mp3$" )
	urlstream = urllib.urlopen( "http://thisamericanlife.org/" )
	processNPRShow( nprParser, urlstream, thumbPathStr, "This American Life" )

# Get the last four (numDaysToGet) episodes of Marketplace
def getMarketPlace():
	def genurl(d):
		urlStr="http://download.publicradio.org/podcast/marketplace/pm/%4d/%02d/%02d/marketplace_podcast_%4d%02d%02d_64.mp3"
		return urlStr % (d.year, d.month, d.day, d.year, d.month, d.day )

	DestFolder = DestDrive + "\\MKTPLC\\"
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
		
	os.chdir("D:\\")    # So USB key isn't locked.

# Weekly shows
getNPRShow( "9911203", '\\CARTALK\\CT_%s.mp3', "Car Talk" )
getNPRShow( "5183214", '\\WW\\WW_%s.mp3', "Wait Wait" )
getTAM( '\\TAM\\TAM_%s.mp3' )

# http://audio.thisamericanlife.org/jomamashouse/ismymamashouse/SHOWNUMBER.mp3
# http://www.sciencefriday.com/audio/scifriaudio.xml

getMarketPlace()