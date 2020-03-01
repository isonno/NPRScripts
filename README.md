PodcastWeek
===========

This script downloads a week's worth of podcasts onto a thumbdrive.

This uses a file in the same folder called "RSSFeeds.txt" to determine what gets loaded. This file is formatted like:
```
# The first item is the folder on the thumbdrive.
# The next item is the "tag" for the MP3 file
#  (i.e., files will be like "JS_25_Nov_17.mp3")
# The last item is the RSS feed for the podcast.
JS,JS,http://textfiles.libsyn.com/rss
```
Checkout `RSSFeeds.txt` for an example I use. Lines starting with "#" are ignored. Usually if you google "Podcastname RSS" and look for a URL ending in `rss` or `xml`, that's it. 

The script pulls up a feed, and downloads all shows with a pub date since the previous Saturday. If you update your thumb drive more often, you'll want to tweak this.

NOTE
====
I've stopped maintaining this for the time being. I now own a phone that works well enough with Android Auto that it's easier to use an app (such as Pocket Casts) to manage the podcasts. The screen interface for listening to MP3s in my Honda is so horrible it's worth the trouble to plug in the phone on every drive.
