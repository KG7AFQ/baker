APRS_SERVER_HOST = 'socal.aprs2.net'
APRS_SERVER_PORT = 14580
APRS_USER = 'myCallSign'
APRS_PASSCODE = 'my5digitAPRSPasscode'
FILTER_DETAILS = "filter g/ProvMar\n"

BAKER_DB = '/var/lib/sqlite/Baker.db' 

# Each packet sent needs to receive an ACKMessage back, if no ACKMessage arrives in SEND-PACKETS_DELAY.Seconds(n), then send the packet again and wait SEND-PACKETS_DELAY.Seconds(n + 1)
SEND_PACKETS_DELAY = [1,10,40,70,130,190,250] # Baker sends n times, waiting for msgack response. Baker only waits for n-1 msgack responses. Effective (send and listen) send times is n-1 

# Check that APRS_USER and APRS_PASSCODE are set
assert len(APRS_USER) > 3 and len(APRS_PASSCODE) > 0, 'Please set APRS_USER and APRS_PASSCODE in settings.py.'

#Baker Commands Lexicon
BAKER_COMMANDS = {
					# Structure - key: [PublishedAS, # of parameters to allow, debug is available]
					#		key - abbreviation for the command to submit to the Baker Server
					#		PublishedAS is used in the pubsub communications as a topic and is also used as the function name to call
					#		# of parameters to allow - the client needs to send this number of string parameters to execute this command on the server
					#		debug is available - if True then send a debug message back to client regarding the validity of this command
					
					'i': ['BakerCmdInsertRunner', 6, True], # Insert or update participant location ex. 'i,ly31,0224,1452107238,1452107238,All is well', insert, station, competitor, time in, time out, comment
					# Reports of person, callSign, support crew (DNF, DNS, last 5 from callsign, etc.)
					'r1': ['BakerCmdReport1', 3, True], # current station, competitor , ex. r1,ly15,022, report1 command, station, competitor
					#Record count by callSign, average MsgACK, server time up, thread count
					'sss': ['BakerCmdServerStatus', 2, False], 
					#Send or Get messages by callSign, Event, Emergency, Baker Help (Held for undetermined amount of time)
					'm': ['BakerCmdMessage',4, True] 
} 
  
# To scan packets with windump on Win 7 machine
# windump -A  -c 1000 -nnvvXSs 0 src or dst 10.0.222.99 and port 51143

# Baker utilizes SQLite for persistent data storage, feature and size requirements are relatively simple
# Baker DB requires the following tables
# CREATE TABLE 'baker_events' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,'dest' TEXT,'src' TEXT, 'station' TEXT, 'competitor' TEXT, 'dtin' DATETIME, 'dtout' DATETIME, 'comment' TEXT, 'dtstamp' DATETIME DEFAULT CURRENT_TIMESTAMP)
# CREATE TABLE 'baker_packets_recd' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,'dest' TEXT,'src' TEXT,'msg' TEXT , 'msgid' TEXT, 'msgack' TEXT, 'aprspacket' TEXT, 'dtarrival' DATE, 'dt_stamp' DATETIME DEFAULT CURRENT_TIMESTAMP)
# CREATE TABLE 'baker_packets_sent' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,'dest' TEXT,'src' TEXT,'msg' TEXT , 'msgid' TEXT, 'msgack' TEXT, msgid_new TEXT, 'aprspacket' TEXT, 'sndcnt' INTEGER, 'dtsent' DATE, 'dt_stamp' DATETIME DEFAULT (datetime('now','localtime')) )
