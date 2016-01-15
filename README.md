# baker

An APRS IS Messaging Server - It is intended to be a tool for Amateur Radio to improve communications at public events.
  
Baker is a server application that facilitates exchanging APRS Message Packets with client software. It stores all packets received, Baker commands received and packets sent. Client software can be any existing APRS client like APRSDroid, Xastir, APRSIS32, YAAC, etc. You send a message from the client and it performs your requests. 
  
For example, to insert a competitor's arrival and departure time at feed zone 5 in the Providence Marathon you would send a message to ProvMar like; 

i,fz5,224,1452107238,1452107560,All is well

The i is for insert, the fz5 is for feed zone 5, bibb number is 224, 1452107238 is time into feed zone (in epoch time) 1452107238, 1452107560 is the time they left the feed zone and last of all a comment of 'all is well'. To fetch this same information you would send another message to ProvMar like 

r1,fz5,224. 

The r1 is for Report 1, fz5 is for feed zone 5 and 224 is the bibb number. The reply rec'd by the client would be 

r1,fz5,224,1452107238,1452107560,All is well.
  
Baker is a messaging server that uses APRS to send and receive messages containing Baker Commands (or protocol). This is an open source project so the protocol can be added to or changed by any competent programmer. The language used is Python which is available on a wide variety of operating systems. Hence, Baker should run well on a wide variety of computer systems. For example, OSX, Linux, BSD and forbid even Windoze.

Baker is even more effective when a APRS client is custom built for an event or radio club. This will allow volunteers to become even more accurate and effecient during a public event.

# Install

Python 2.7 is the language used to write baker. It could run on Python 3 but the differences between the two is a huge topic of discussion. My take is that 2.7 has been around awhile and is deeply embedded in OSes and other significan applications. To convert to Python 3 could be done without much effort by a competent programmer. Do not confuse Python 3 with SQLite 3. There is no relationship between these versions except in their naming scheme.::
	Install Python if you need to. Most Linux systems have Python installed.

Place all files from the Github repository into the directory of your choice.

Install any python libraries (see the imports in baker.py)

To use libfap.py you must install libfap C libraries. Here is their URL http://www.pakettiradio.net/libfap/.::
	(In libfap.py lines 6 and or 7 may need to be adjusted after you install libfap C, one of these should work)
	(See this page for changes that may be require to libfap.py V1.5 1/25/2015 https://www.raspberrypi.org/forums/viewtopic.php?t=44930&p=356499)

To use apsw (SQLite interface for Python) check the details from APSW docs at https://rogerbinns.github.io/apsw/ I have been using V3.8 (stable) in my latest efforts. (APSW is used instead of pysqlite because APSW handles threading better. It does not handle it perfectly but better. I am watching for a release from APSW or pysqlite that is completely thread safe)

To use pubsub see http://pubsub.sourceforge.net/installation.html . It should install with little effort. (It is a publish / subscribe communications library for Python. It greatly simplifies thread to thread and class to class code usage and code use in general)

## Configure / Run

Edit the settings.py file to personalize your communications server.::
	APRS_USER should be your callsign or an station callsign
	APRS_PASSCODE should be a passcode created using the callsign in APRS_USER
	FILTER_DETAILS = "filter g/?????\n". Don't use ProvMar. Create your own. This is the quasi callsign that you will use to communicate with clients. A club name or an event name would be a good choice. Multiple filters can be included in this variable. Make sure the callsign in Filter_Details is in upper case.

The APRS_SERVER_HOST could be set to "rotate.aprs2.net" but since your clients will probably be local to the baker server, I suggest you use a Tier2 APRS server nearest you. This would keep packet travels back and forth from the clients to a much smaller area than the world over. It's default setting is to southern California. If you can persuade the APRS clients to use the same Tier2 server than you are even more organized than I am.

Run from the command line by executing "baker.py". It can be done in a number of ways. "python baker.py", "./baker.py" if the file is set to executable. It could also be run on boot as well. A competent linux administrator can help you with this.

## Operation

There are a few commands can be run interactively from the console to interact with baker. ::
	q //<Return> will cause baker to halt operations. This takes a moment as the threads are brought down gracefully.
	t /<cr> will cause a test packet to be sent from baker to the SendQ and sent to a given client client from FILTER_DETAILS. Make sure the callsign in Filter_Details is in upper case.