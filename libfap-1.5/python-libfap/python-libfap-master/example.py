#!/bin/python
# 
# see this page for changes to libfap.py V 1/25/2015 https://www.raspberrypi.org/forums/viewtopic.php?t=44930&p=356499
import socket
import re
from datetime import datetime 

from libfap import *
import settings

debug1 = 2;

# create socket & connect to server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((settings.APRS_SERVER_HOST, settings.APRS_SERVER_PORT))

# logon to APRS-IS Server
login = 'user %s pass %s libfap-python testing V.01/25/2015 %s'  % (settings.APRS_USER, settings.APRS_PASSCODE , settings.FILTER_DETAILS)
sock.send(login)    
sock_file = sock.makefile()
libfap.fap_init()

# initial response by aprs-is server
packet_str = sock_file.readline()
packet = libfap.fap_parseaprs(packet_str, len(packet_str), 0)
libfap.fap_free(packet)
packet_str = sock_file.readline()
packet = libfap.fap_parseaprs(packet_str, len(packet_str), 0)

print ('\nBAKER Server - 2015 - Brian - KG7AFQ - V0.1')
print ('\n%s - APRS-IS Server > login greeting [%s %s]\n' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), packet[0].orig_packet.strip('\r\n'), packet[0].orig_packet.strip('\r\n') ))

libfap.fap_free(packet)

# listen for all subsequent packets from aprs-is server
try:
	while 1:
		packet_str = sock_file.readline()
		packet = libfap.fap_parseaprs(packet_str, len(packet_str), 0)
        
		if packet[0].destination == None:
			if debug1 > 1:
				print ('%s APRS-IS > message - [packet,%s]' % (datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S'), packet[0].orig_packet.strip('\r\n')))
				print ('%s APRS-IS > message - [non-message packet]\n' % (datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S') ))
			print ('%s APRS-IS > non-message - []' % (datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')) )
		else: # Valid packet, ack or not, then parse message itself
			if debug1 > 0:				
				print('%s APRS-IS > message - [from, to, message, id - %s, %s, %s, %s' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), packet[0].src_callsign, packet[0].destination, packet[0].message, packet[0].message_id ) )
				print('%s APRS-IS > message - [packet - %s' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), packet[0].orig_packet) )
			if (packet[0].message_id != None): #ack it
				print('%s APRS-IS < ack - [%s>APZ009,WIDE1-1,WIDE2-1::%s:ack%s]' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), packet[0].destination, packet[0].src_callsign.ljust(9,' '), packet[0].message_id))
				sock_file.write("%s>APZ009,WIDE1-1,WIDE2-1::%s:ack%s\r\n" % (packet[0].destination, packet[0].src_callsign.ljust(9,' '), packet[0].message_id))
				sock_file.flush()
			sock_file.write("%s>APZ009,WIDE1-1,WIDE2-1::%s:Your msg was-%s\r\n" % (packet[0].destination, packet[0].src_callsign.ljust(9,' '), packet[0].message))
			sock_file.flush()

		libfap.fap_free(packet)
except KeyboardInterrupt:
		pass

libfap.fap_cleanup()

# close socket -- must be closed to avoid buffer overflow
sock.shutdown(0)
sock.close()
