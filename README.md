# baker

  An APRS IS Messaging Server - 
  
  Baker uses a protocol to exchange APRS Packets with client software. Client software can be any existing APRS client like APRSDroid, Xastir, APRSIS32, YAAC, etc. It can be used from the messaging menus of these client applications. You send a message and it performs your requests. For example, to insert a competitor's arrival and departure time at feed zone at feed zone 5 in the RagShagMarathon you would send a message to RagShag like i,fz5,224,1452107238,1452107560,All is well. The i is for insert, the fz5 is for feed zone 5, bibb number is 224, time into feed zone (in epoch time) 1452107238, time left feed zone (in epoch time) 1452107560 and a comment of 'all is well'. To fetch this same information you would send another message to RagShag like r1,fz5,224. The r1 is for Report 1, fz5 is for feed zone 5 and 224 is the bibb number. The reply rec'd by the client would be r1,fz5,224,1452107238,1452107560,All is well.
  
  Baker is a Messaging Server that uses APRS to send messages that contain Baker Commands or use the Baker Protocol. This is an open source project so the protocol can be added to or changed by any competent programmer. The language used is Python which is available on a wide variety of operating systems. Hence, Baker should run on a wide variety of operating systems. For example, OSX, Linux, BSD and forbid even Windoze.


