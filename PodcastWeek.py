#!/usr/bin/python3
#
# Podacast week. Downloads a week's worth of podcasts onto a thumbdrive.
#
# This uses a file in the same folder called "RSSFeeds.txt" to determine
# what gets loaded. This file is formatted like:
# JS,JS,http://textfiles.libsyn.com/rss
# The first item is the folder on the thumbdrive.
# The next item is the "tag" for the MP3 file
#  (i.e., files will be like "JS_25_Nov_17.mp3")
# The last item is the RSS feed for the podcast.
#
# Usually if you google "Podcastname RSS" and look for a URL
# ending in "rss" or "xml", that's it.  Lines starting with "#" are ignored.
#
# The script pulls up a feed, and downloads all shows with a pub date
# since the previous Saturday. If you update your thumb drive more often,
# you'll want to tweak this.
#
# John Peterson, Nov 2017. This is a major re-write of "GetMktplc.py"
#

import string, time, urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, os, sys
import xml.dom.minidom as xml
import datetime, string, glob

# Pull data from XML item. If it's an attribute
# (not the data) passing "key,attr" in the key works.
def getData(item, key, attr=None):
    if (not attr) and (key.find(",") > 0):
        [key, attr] = key.split(",")

    itemData = item.getElementsByTagName(key)
    if (len(itemData) == 0):
        return None
    itemData = itemData[0]

    if (attr):
        return itemData.getAttribute(attr)
    else:
        return itemData.firstChild.data if itemData.firstChild else None

# One podcast show
class Show:
    def __init__(self, xml):
        self.data = {}
        def keyRoot(s):
            s = s.replace("itunes:","")
            s = s.replace(":","_")
            return s.replace(",","_")

        # This is collection of keys I found...
        keys = ["pubDate", "title", "link", "description",
                "enclosure,url", "enclosure,length", "itunes:subtitle",
                "itunes:episode", "itunes:image,href", "itunes:duration",
                "media:content,url", "content:encoded"]

        # ...but only these keys are used consistently across *all* feeds
        keys = ["title", "description", "pubDate", "enclosure,url",
                "itunes:duration"]

        for k in keys:
            self.data[keyRoot(k)] = getData(xml, k)
        # Skip timezone, %z is broken in python 2.7
        self.date = datetime.datetime.strptime(self.data['pubDate'][:25], "%a, %d %b %Y %H:%M:%S")
        self.date = self.date.date()

    def download(self, base, folder):
        mp3url = self.data['enclosure_url']
        dstName = base + "_" + self.date.strftime("%d_%b_%y") + ".mp3"
        dstpath = DestDrive + os.sep + folder + os.sep + dstName
        dupe_count = 0
        while (os.path.exists(dstpath) and dupe_count < 20):
            print("# Already have %s" % dstName)
            dstpath = DestDrive + os.sep + folder + os.sep + ("%02d_" % dupe_count) + dstName
            dupe_count += 1
        if self.data['enclosure_url']:
            if (dupe_count > 0):
                print("# Writing show %s\n  (%s)" % (("%02d_" % dupe_count) + dstName, self.data['title']))
            else:
                print("# Writing show %s\n  (%s)" % (dstName, self.data['title']))
            showStream = None
            try:
                showStream = urllib.request.urlopen(self.data['enclosure_url'])
                showMP3 = showStream.read()
                open(dstpath, 'wb').write(showMP3)
            except urllib.error.URLError as err:
                print("### RE-DIRECT Failure?? %s" % str(err))
                print("Original URL %s" % self.data['enclosure_url'])
                if (showStream):
                    print("Redirect URL %s" % showStream.geturl())
        else:
            print("# No MP3 available for (%s)" % self.data['title'])

    # Debug
    def ShowKeys(self):
        print(string.join([k for k in list(self.data.keys()) if (self.data[k])], " : "))

# Podcast feed info
class PodFeed:
    def __init__(self, dir, baseName, feedURL):
        self.dir = dir
        self.url = feedURL
        self.baseName = baseName
        xmltext = ""
        try:
            xmltext = urllib.request.urlopen( feedURL ).read()
        except IOError:
            print("Failed to read: %s" % feedURL)
            sys.exit(0)

        xmldata = xml.parseString( xmltext )
        for k in ["title", "link", "description"]:
            self.__dict__[k] = getData(xmldata, k)

        print("Loading RSS for %s" % self.title)

        # For now, assume shows are in reverse chron order,
        # we could sort to be super sure...
        items = xmldata.getElementsByTagName("item")
        self.shows = [Show(item) for item in items]

def getWindowsDrives():		# http://stackoverflow.com/questions/827371
	from ctypes import windll
	drives = []
	bitmask = windll.kernel32.GetLogicalDrives()
	for letter in string.ascii_uppercase:
		if bitmask & 1:
			drives.append(letter + ":")
		bitmask >>= 1

	return drives

DestDrive = None

def setDestinationDrive():
	global DestDrive
	if sys.platform == "darwin":
		DestDrive = "/Volumes/AUDIO"
		if not os.path.exists(DestDrive):
			print("Thumb drive %s not plugged in?" % DestDrive)
			sys.exit(-1)
	else:
		winDrives = getWindowsDrives()[1:]	# Skip the C: drive
		for d in winDrives:
			if (os.path.exists( d + os.path.sep + "MKTPLC" )):
				DestDrive = d
				break
		if (not DestDrive):
			print("NPR Thumb drive missing?  It must have a MKTPLC folder")
			sys.exit(-1)

# Return the date of the last specified weekday (0=Mon, 1=Tue...6=Sun)
def lastNday(n):
	return (datetime.date.today() - datetime.timedelta( datetime.date.today().weekday()+(7-n) ))

# Clean shows off the drive (run before loading new shows)
def clean():
	folders = ["99PI", "PM", "CARTALK", "FAIR", "FNR", "JS", "MKTPLC", "INVIS", "RT", "GIM", "SCIFRI", "TAM", "TED", "WW"]
	for fold in folders:
		path = DestDrive + os.path.sep + fold + os.path.sep
		if not os.path.exists( path ):
			print("Creating folder %s..." % path)
			os.mkdir( path )
		else:
			print("Cleaning %s..." % path)
			[os.remove(path + f) for f in os.listdir( path )]

def downloadShows():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    feedtext = open("RSSFeeds.txt",'r').readlines()
    feeds = []
    print("# Loading RSS feeds...")
    for t in feedtext:
        if (t[0] != "#"):
            args = (t[:-1]).split(",")
            feeds += [PodFeed(args[0], args[1], args[2])]

    lastDay = lastNday(0)
    for f in feeds:
        for show in f.shows:
            if show.date > lastDay:
                show.download(f.baseName, f.dir)

def main():
    setDestinationDrive()
    if (len(sys.argv) > 1 and sys.argv[1] == "clean"):
        clean()
    else:
        downloadShows()

main()
