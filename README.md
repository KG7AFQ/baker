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

#Install

Place all files in the directory of your choice.

Install any python libraries you may need. 
