NPRScripts
==========

*UPDATE* - check out the new script, `PodcastWeek.py`. More details when, uh, I get a chance to work on it again.

I like to listen to NPR podcasts in my car.  About once a week, I plug in a thumb drive to my PC and run this
script, which gathers up shows I like and downloads them to the thumb drive.

On the Mac, the thumb drive should have the volume name `AUDIO`.  On Windows, it searches the mounted volumes
(except the first one, typically `C:`) for a top level folder called `MKTPLC`.

Currently it grabs the weekly shows ~~Car Talk~~, Wait Wait, Freakanomics, ~~Serial~~, ~~Invisibilia~~ and This American Life, as well as the last four weekday shows of Marketplace and the last two episodes of Planet Money.  Marketplace was the first show I wrote the script for, hence the name "GetMktplace".

Usage:

*  `GetMktplace.py`               Loads shows onto the thumb drive
*  `GetMktplace.py clean`         Deletes all previously downloaded shows
*  ~~`GetMktplace.py tam NNN`     Download [This American Life](http://www.thisamericanlife.org/) episode NNN~~
