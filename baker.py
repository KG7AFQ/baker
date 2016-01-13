#!/usr/bin/python

#Copyright (c) 2015, Brian Marble, KG7AFQ, 
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
#1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
#2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer
#	in the documentation and/or other materials provided with the distribution.
#
#3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived 
#	from this software without specific prior written permission.

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, 
#	BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
#	IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, 
#	OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, 
#	OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
#	OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 
import socket, traceback, sys, copy, re
from datetime import datetime, timedelta 
import threading
import time
import select
import apsw # sqlite library w/threading support	
from pubsub import pub
# see this page for changes to libfap.py V 1/25/2015 https://www.raspberrypi.org/forums/viewtopic.php?t=44930&p=356499
from libfap import *
import settings


############################
# Classes
############################
class clsBakerMessage():

	def __init__(self, src, dest, msg, msgid, msgack, orig_packet, dtarrival, key=''):
		try:
			self.src = src.upper()
			self.dest =  dest.upper()
			self.msg = msg.replace("'","?").replace('"','?') # replace single and double quotes with question mark
			self.msgid = msgid
			self.msgack = msgack # To match msgack in ReceiveQ to item sent from Send Q, use key
								 # Item in SendQ with key is waiting for msgack in Recieive Q where SendQ.key (SendQ.src + SendQ.msgid_new) =  ReceiveQ[item].dest +  ReceiveQ[item].msg[3:]
			self.orig_packet = orig_packet
			self.aprspacket = unicode(orig_packet, 'ISO-8859-1')
			self.dtarrival = dtarrival
			self.dtsent = datetime(2000, 1, 1, 0, 0, 0)
			self.msgid_new =  str(int(round(time.time()*10**6)))[-5:] # Not alwasys used, for sending Baker Command Response Packets to client
			self.key = self.src + self.msgid_new
			self.type = ' '
			self.dtfirstsent = datetime(2000, 1, 1, 0, 0, 0)
			self.snddelays = settings.SEND_PACKETS_DELAY
			self.sndcnt = 0
			self.isValidBakerMessage = True
			if debuglevel > 0: 
				print('%s APRS-IS > Baker Packet - [src, dest, msg, msgid, msgid_new, msgack, key, type, arrival - [%s, %s, %s, %s, %s, %s, %s, %s, %s]' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), self.src, self.dest, self.msg, self.msgid, self.msgid_new, self.msgack, self.key, self.type, self.dtarrival) )
		except Exception as error:
			print ('exception clsBakerMessage')
			traceback.print_exc()
			self.isValidBakerMessage = False
	
class clsBakerPacket():
	
	def __init__(self, pkt):
		try:
			# Is there a packet?
			# Check validity of packet
			self.isValidBakerPacket = False
			if pkt[0].orig_packet.find('#') == 1: 
				# This is a keep alive message from APRS-IS server (APRS Packet with first char of '#') ignore it
				if debuglevel > 0:
					print ('%s APRS-IS > non-message - [keep-alive from APRS Server]' % (datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')) )
				self.isValidBakerPacket = False
			elif pkt[0].destination == None: 
				# This is a non valid Message Packet
				if debuglevel > 1: 
					print ('%s APRS-IS > message - [packet,%s]' % (datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S'), pkt[0].orig_packet.strip('\r\n')))
					print ('%s APRS-IS > message - [non-message packet]\n' % (datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S') ))
				print ('%s APRS-IS > non-message - []' % (datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')) )
				self.isValidBakerPacket = False
			else: 
				# This is a valid message packet
				if pkt[0].message:
					self.dest =  pkt[0].destination
					self.src = pkt[0].src_callsign
					self.orig_packet = pkt[0].orig_packet
					self.msg = pkt[0].message
					self.msgid = pkt[0].message_id
					self.msgack = pkt[0].message_ack
					self.dst = pkt[0].dst_callsign
					self.path = pkt[0].path
					self.comment = pkt[0].comment
					if (self.msg.find('{') > 1 and self.msg.find('}') > 1 and self.msgid == None):
						# Work around libfap shortcomings
						# APRS "REPLY-ACK" is not handled by libfap, must be adjusted here until libfap fixes bug, APRSIS32 is only one found to have this anomoly as of 11/2015	
						# order is important
						self.msgid = self.msg[self.msg.find('{') + 1:] 
						self.msg =  self.msg[:self.msg.find('{')] 
					self.isValidBakerPacket = True
					if self.isValidBakerPacket == True:
						# Create Baker Message
						self.BkrMsg = clsBakerMessage(self.src, self.dest, self.msg, self.msgid, self.msgack, self.orig_packet, datetime.now())
						# Save msg to DB
						pub.sendMessage('RecSaveDB', arg1=self.BkrMsg)
						# Dispatch Baker Message
						bmsgcopy = copy.copy(self.BkrMsg)
						self.dispatchMessage(bmsgcopy)
					#else:
					#	print('%s APRS-IS > invalid packet - [Houston, we have a problem' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')) )
		except Exception, err:
			print ('exception clsBakerPacket')
			traceback.print_exc()
			print ('pkt[0] - %s' % pkt[0])
			self.isValidBakerPacket = False
			
	def dispatchMessage(self, bmsg):
		#bmsg = arg1
		try:		
			# Either ACK it and push it into the Baker Command Queue or send it to the SendQ to be matched
			if bmsg.msgid: 
				# Send to SendQ so an ack will be delivered
				bmsg.type = 'Need2ACK'
				bmsgcopy1 = copy.copy(bmsg)
				pub.sendMessage('Need2ACK', arg1=bmsgcopy1)
				# Process Baker Command
				bmsgcopy2 = copy.copy(bmsg)
				bmsgcopy2.type = 'BakerCmdResponse'
				pub.sendMessage('NewBakerCmd', arg1=bmsgcopy2)
			elif bmsg.msgack:
				# This packet is rec'd from the client. It is a response to any Baker Message sent to the client.
				# It needs to be matched with the original Baker message in the SendQ, otherwise the SendQ will send another out.
				bmsg.type = 'MsgACK'
				bmsgcopy = copy.copy(bmsg)
				pub.sendMessage('MsgACK', arg1=bmsgcopy)
		finally:
			pass

class clsBakerCommand():

	def __init__(self):
		pub.subscribe(self.NewBakerCmd,'NewBakerCmd')
		self.bkrCmds = settings.BAKER_COMMANDS
		self.lstCmd = ()

	def NewBakerCmd(self, arg1):
		bmsg = arg1
		self.lstCmd = bmsg.msg.split(',')
		cmdKey = self.lstCmd[0]
		if cmdKey in self.bkrCmds:
			if debuglevel > 1:
				print 'valid baker command - ', self.bkrCmds[cmdKey][0], self.bkrCmds[cmdKey][1], self.bkrCmds[cmdKey][2] 
			if len(self.lstCmd) == self.bkrCmds[cmdKey][1]:
				if debuglevel > 0:
					print ('%s %s - A [%s, from %s]' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),'APRS IS > Baker Command ', bmsg.msg, bmsg.src))
				pub.sendMessage(self.bkrCmds[cmdKey][0], arg1=bmsg, arg2=self.lstCmd)
		else:
			if debuglevel > 0:
				print ('%s %s - A [%s, %s, %s, %s]' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),'APRS IS > Baker Command N/A', bmsg.src, bmsg.dest, bmsg.msg, bmsg.msgid))
							
class clsAPRSConnection():

	def __init__(self):
		try:
			# Create socket & connect
			self.connected = False
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.connect((settings.APRS_SERVER_HOST, settings.APRS_SERVER_PORT))
			self.name = 'clsAPRSConnection'
			pub.subscribe(self.PacketSend, 'PacketSend')
			
			# Logon to APRS-IS Server
			login = 'user %s pass %s BAKER V.01 01/12/2016 %s '  % (settings.APRS_USER, settings.APRS_PASSCODE, settings.FILTER_DETAILS)
			self.sock.send(login)
			self.sock_file = self.sock.makefile()
			libfap.fap_init()

			# handle initial response by aprs-is server
			packet_str = self.sock_file.readline()
			packet = libfap.fap_parseaprs(packet_str, len(packet_str), 0)
			print ('\n%s - APRS-IS Server > login greeting [%s %s]\n' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), packet[0].orig_packet.strip('\r\n'), packet[0].orig_packet.strip('\r\n') ))
			libfap.fap_free(packet)
			packet_str = self.sock_file.readline()
			packet = libfap.fap_parseaprs(packet_str, len(packet_str), 0)
			libfap.fap_free(packet)
			self.connected = True
		except Exception, err: 
			print ('exception in clsAPRSConnection')
			traceback.print_exc()
			# close socket
			self.connected = False
			if self.sock:
				self.sock.shutdown(0)
				self.sock.close()

	def PacketSend(self, arg1):
		pkt2Send = arg1
		try:
			self.sock_file.write(pkt2Send+ '\r\n')
			self.sock_file.flush()
		except Exception as error:
			print('exception in clsAPRSConnection.PacketSend')
			print ('sys.exc_info()[0] - ',sys.exc_info())

class clsBakerDB():
	
	def __init__(self):
		try:
			if debuglevel > 1:
				print "\nUsing APSW file",apsw.__file__   # from the extension module
				print "APSW version",apsw.apswversion() # from the extension module
				print "SQLite lib version",apsw.sqlitelibversion() # from the sqlite library code
				print "SQLite header version",apsw.SQLITE_VERSION_NUMBER # from the sqlite header file at compile time
			self.dbcon = apsw.Connection(settings.BAKER_DB) 
			self.lastrowid = 0
			self.seconds = 6 # time to sleep before final close of DB
			pub.subscribe(self.close, 'ShutdownDB')
			pub.subscribe(self.bmRecSave, 'RecSaveDB')
			pub.subscribe(self.bmSendSave, 'SendSaveDB')
			pub.subscribe(self.BakerCmdInsertRunner, 'BakerCmdInsertRunner')
			pub.subscribe(self.BakerCmdReport1, 'BakerCmdReport1')
		except apsw.Error, e:
			print "APSW error - all args:", e.args
			self.dbcon = False		
			print "Error - clsBakerDB %s:" % e.args[0]
			if self.dbcon:
				self.dbcon.close()

	def bmRecSave(self, arg1):
		#save rec'd Baker Packet to DB Table
		bmsg = arg1
		data = (bmsg.dest, bmsg.src, bmsg.msg, bmsg.msgid, bmsg.msgack, bmsg.aprspacket, str(bmsg.dtarrival))
		if self.dbcon:
			cur = self.dbcon.cursor()
			try:
				#insert into db table
				cnt = cur.execute ("insert into baker_packets_recd (dest, src, msg, msgid, msgack, aprspacket, dtarrival) values (?,?,?,?,?,?,?)", data)
				cnt = self.dbcon.last_insert_rowid()
				if cnt > 0:
					self.lastrowid = self.dbcon.last_insert_rowid()
				if debuglevel > 1:
					cur.execute('SELECT * from baker_packets_recd order by id desc limit 10')
					rows = cur.fetchall()
					print 'Last 10 Baker Packets Sent'
					for row in rows:
						print row		
			except apsw.Error as error:
				print "SQLite error at bmRecSave - all args:", error, error.args
				self.bmRecSave = False	
			except Exception as error:
				print ('exception clsBakerDB.bmRecSave')
				traceback.print_exc() 
				print ('sys.exc_info()[0] - ',sys.exc_info()[0])
		else:
			print 'db connection is down'
			
	def BakerCmdInsertRunner(self, arg1, arg2):
		bmsg = arg1
		lstbcmd = arg2
		if self.dbcon:
			cur = self.dbcon.cursor()
			try:
				# find existing record first, if there is not one then insert it
				data = (lstbcmd[1], lstbcmd[2])
				cnt = 0
				for id, dest, src, station, competitor, dtin, dtout, comment in (cur.execute ("select id, dest, src, station, competitor, dtin, dtout, comment from baker_events where station = ? and competitor = ? limit 1", data)):
					cnt = 1
					# The record exists, so change the values and update it
					newdtin = str(lstbcmd[3])
					newdtout = str(lstbcmd[4])
					newcomment = lstbcmd[5]
					if newdtin <> dtin:
						tmpcomment = "Prev In:" + str(dtin)
					if newdtout <> dtout:
						tmpcomment = tmpcomment + " Prev Out:" + str(dtout)
					if newcomment <> comment:
						tmpcomment =  newcomment + " " + tmpcomment
					if tmpcomment:
						newestcomment = tmpcomment + " " + comment
					data = (BakerCommon.epoch2iso8601time(newdtin), BakerCommon.epoch2iso8601time(newdtout), newestcomment, lstbcmd[1], lstbcmd[2])
					cur.execute("update baker_events set dtin = ?, dtout = ?, comment = ? where station = ? and competitor = ? limit 1", data)
				if cnt == 0:
					# The record does not exist so insert it
					data = (bmsg.dest, bmsg.src, lstbcmd[1], lstbcmd[2], BakerCommon.epoch2iso8601time(lstbcmd[3]), BakerCommon.epoch2iso8601time(lstbcmd[4]), lstbcmd[5]) 
					rows = cur.execute ("insert into baker_events (dest, src, station, competitor, dtin, dtout, comment) values (?,?,?,?,?,?,?)", data)
					print 'inserted new row - ', data
				if debuglevel > 0:
					print 'Last 10 Baker Commands Received'
					cur.setrowtrace(self.rowtrace)
					for row in cur.execute('SELECT dest, src, station, competitor, dtin, dtout, comment from baker_events order by id desc limit 10'):
						pass
					cur.setrowtrace(None)		
			except apsw.Error as error:
				print "SQLite error at bmRecSave - all args:", error, error.args
				self.bmRecSave = False	
			except Exception as error:
				print ('exception clsBakerDB.bmRecSave')
				traceback.print_exc() 
				print ('sys.exc_info()[0] - ',sys.exc_info()[0])
		else:
			print 'db connection is down'
	
	def BakerCmdReport1(self, arg1, arg2):
		bmsg = arg1
		lstbcmd = arg2
		if debuglevel > 0:
			print 'Baker Command List - ', lstbcmd 
		if self.dbcon:
			cur = self.dbcon.cursor()
			try:
				# find existing record first, if there is not one then insert it
				data = (lstbcmd[1], lstbcmd[2])
				cnt = 0
				for id, dest, src, station, competitor, dtin, dtout, comment in (cur.execute ("select id, dest, src, station, competitor, dtin, dtout, comment from baker_events where station = ? and competitor = ? ", data)):
					cnt = 1
					# The record exists, so change the values and update it
					msgnew = "r1".encode('utf-8') + "," + station.encode('utf-8') + "," + competitor.encode('utf-8') + "," + BakerCommon.iso86012epochtime(dtin.encode('utf-8')) + "," + BakerCommon.iso86012epochtime(dtout.encode('utf-8')) + "," + comment.encode('utf-8')
					bmsgnew = clsBakerMessage(bmsg.dest, bmsg.src, msgnew, None, None, "Internal", datetime.now())
					bmsgnew.type = 'BakerCmdResponse'
					pub.sendMessage('Add2SendQ',arg1=bmsgnew)
				if cnt == 0:
					# The record does not exist 
					if debuglevel > 1:
						print 'BakerCmdReport1, no result'
				if debuglevel > 1:
					print 'Last 10 Baker Packets Sent'
					cur.setrowtrace(self.rowtrace)
					for row in cur.execute('SELECT dest, src, station, competitor, dtin, dtout, comment from baker_events order by id desc limit 10'):
						pass
					cur.setrowtrace(None)		
			except apsw.Error as error:
				print "SQLite error at bmRecSave - all args:", error, error.args
				self.bmRecSave = False	
			except Exception as error:
				print ('exception clsBakerDB.bmRecSave')
				traceback.print_exc() 
				print ('sys.exc_info()[0] - ',sys.exc_info()[0])
		else:
			print 'db connection is down'
	
	def rowtrace(self, cursor, row):
		"""Called with each row of results before they are handed off.  You can return None to
			cause the row to be skipped or a different set of values to return"""
		print "Row:", row
		return row
			
	def bmSendSave(self, arg1):
		#save sent Baker Packet to DB Table
		bmsg = arg1
		self.saved_valid_message = False
		cur = self.dbcon.cursor()
		try:
			# Find existing record (using bmsg)
			data = (bmsg.msgid_new)
			rows = list(cur.execute ("select id from baker_packets_sent where msgid_new = ?", [data]))
			cnt = len(rows)
			if cnt == 0:			
				# Insert new record 
				data = (bmsg.dest, bmsg.src, bmsg.msg, bmsg.msgid, bmsg.msgack, bmsg.msgid_new, bmsg.aprspacket, bmsg.sndcnt, str(bmsg.dtsent))
				rows = list(cur.execute ("insert into baker_packets_sent (dest, src, msg, msgid, msgack, msgid_new, aprspacket, sndcnt, dtsent) values (?,?,?,?,?,?,?,?,?)", data))
				cnt = len(rows)
			else:
				# Update existing record 
				data = (bmsg.sndcnt, bmsg.msgid_new)
				rows = list(cur.execute ("update baker_packets_sent set sndcnt = ? where msgid_new = ?", data))
			if cnt > 0:
				self.saved_valid_message = True
			if debuglevel > 1:
				rows = list(cur.execute('SELECT * from baker_packets_sent order by id desc limit 10'))
				print 'Last 10 Baker Packets Sent'
				for row in rows:
					print row		
		except apsw.Error as error:
			print "SQLite error at bmSendSave - all args:", error, error.args
			self.bmSendSave = False	
		except Exception as error:
			print ('exception clsBakerDB')
			traceback.print_exc() 
			print ('sys.exc_info()[0] - ',sys.exc_info()[0])
			
	def close(self):
		if self.dbcon:
			self.dbcon.close()
		print('%s %s - Terminating' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), 'DB Connection'))

class thrdSendPacketQ(threading.Thread):

	def __init__(self, name, seconds, que):
		threading.Thread.__init__(self)
		self.name = name 
		self.seconds = seconds
		self.que = que
		self.exit = False
		pub.subscribe(self.close, 'Shutdown')
		pub.subscribe(self.Add2SendQ, 'Add2SendQ')
		pub.subscribe(self.Need2ACK, 'Need2ACK')
		pub.subscribe(self.SendTestPacket, 'SendTestPacket')
		pub.subscribe(self.MsgACK, 'MsgACK')
		
	def run(self):
		#global intExitFlag
		print ('%s %s - Starting' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), self.name))
		self.thread_ident = threading.current_thread().ident
		while not self.exit:
			time.sleep(self.seconds)
			if debuglevel > 0:
				print ('%s %s - Count %s' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),'Baker - SendQ ', len(self.que)))
			if self.que:
				self.CheckAndProcessQ()
		print('%s %s - Terminating' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), self.name))
		return

	def CheckAndProcessQ(self):
		lDelete = []
		for k, bmsg in self.que.items():
			if debuglevel > 0: 
				print('%s APRS-IS > Baker Send Q item - [src, dest, msg, msgid, msgid_new, msgack, key, type, arrival - [%s, %s, %s, %s, %s, %s, %s, %s, %s]' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), bmsg.src, bmsg.dest, bmsg.msg, bmsg.msgid, bmsg.msgid_new, bmsg.msgack, bmsg.key, bmsg.type, bmsg.dtarrival) )
		for k, bmsg in self.que.items():
			if bmsg.type == 'Need2ACK':
				# Send ACK to this message, only send it once. If they do not receive this ACK, they will request another APRS Packet
				pub.sendMessage('PacketSend', arg1=bmsg.aprspacket)
				# Save msg to DB
				bmsgcopy = copy.copy(bmsg)
				pub.sendMessage('SendSaveDB', arg1=bmsgcopy)
				if debuglevel > 0: 
					print("%s APRS-IS < ACK [%s]" % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), bmsg.aprspacket))
				lDelete.append(bmsg.key)
			elif bmsg.type == 'MsgACK': 
				# Match and Delete
				lDelete.append(bmsg.key) 
				print('%s %s - ACK Matched - [key - %s]' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), self.name, bmsg.key))
			elif bmsg.type == 'BakerCmdResponse': 
				# Send Baker Command Response Packets to requesting clients
				dtnow = datetime.now()
				# Only send when current time is greater than datefirstsent + snddelays(n)
				if  (bmsg.sndcnt == 0) or (dtnow > bmsg.dtfirstsent + timedelta(seconds=bmsg.snddelays[bmsg.sndcnt])):
					if bmsg.sndcnt == 0:
						bmsg.dtfirstsent = dtnow
					if debuglevel > 0:
						print ('%s %s - Attempt %s/%s [%s, %s, %s, %s, %s]' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),'APRS IS < Send Baker Packet', bmsg.sndcnt + 1, len(bmsg.snddelays) ,bmsg.src, bmsg.dest, bmsg.msg, bmsg.msgid, bmsg.dtarrival))
					bmsg.aprspacket = ("%s>APZ009,TCPIP*::%s:%s%s" % (bmsg.src.strip(), '{0: <9}'.format(bmsg.dest), bmsg.msg + '{', bmsg.msgid_new))
					bmsg.dtsent = datetime.now()
					bmsg.sndcnt += 1
					pub.sendMessage('PacketSend', arg1=bmsg.aprspacket)
					# Save msg to DB
					bmsgcopy = copy.copy(bmsg)
					pub.sendMessage('SendSaveDB', arg1=bmsgcopy)
					# Delete from Q - tried to send the max number of times
					if bmsg.sndcnt == len(bmsg.snddelays):
						lDelete.append(bmsg.key)
					if debuglevel > 0: 
						print("%s APRS-IS < Baker Response [%s]" % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), bmsg.aprspacket))
		# Delete items in sendQ as found in lDelete
		for key in lDelete:
			del self.que[key]
	
	def Add2SendQ(self, arg1):
		bmsg = arg1
		self.que[bmsg.key] = bmsg
	
	def Need2ACK(self, arg1):
		# Ack Rec'd Message - convert bmsg from rec'd to sendable
		bmsg = arg1
		bmsgnew = clsBakerMessage(bmsg.src, bmsg.dest, 'ack' + bmsg.msgid, None,None, bmsg.orig_packet, bmsg.dtarrival)
		bmsgnew.type = 'Need2ACK'
		bmsgnew.dtfirstsent = datetime.now()
		bmsgnew.aprspacket = ("%s>APZ009,TCPIP*::%s:%s" % (bmsgnew.dest.strip(), '{0: <9}'.format(bmsgnew.src), bmsgnew.msg)) #ACK only
		bmsgnew.dtsent = bmsg.dtfirstsent
		bmsgnew.sndcnt = 1
		self.Add2SendQ(bmsgnew)
	
	def MsgACK(self, arg1):
		# Create key to match MsgACK Baker Packet to existing Baker Packet in SendQ. Send to SendQ
		bmsg = arg1
		bmsg.key = bmsg.dest + bmsg.msg[3:]
		self.Add2SendQ(bmsg)
	
	def SendTestPacket(self, arg1):
		bmsg = clsBakerMessage('ProvMar', '{0: <9}'.format('KG7AFQ-9'), 'Testing BAKER APRS-IS Application Server - Providence Marathon Test Case', None, None, 'Test orig_packet', datetime.now())
		bmsg.type = 'BakerCmdResponse'
		self.Add2SendQ(bmsg)
		if debuglevel > 0:			
			print ('%s %s - [%s, %s, %s, %s, %s, %s]' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),'APRS IS < Test Packet', bmsg.src, bmsg.dest, bmsg.msg, bmsg.msgid, bmsg.msgid_new, bmsg.dtarrival))

	def close(self):		
		self.exit = True

class thrdKeyboardPollerChars(threading.Thread):
	
	def __init__(self, name, seconds):
		threading.Thread.__init__(self)
		self.seconds = seconds
		self.name = name
		self.exit = False
		pub.subscribe(self.close, 'Shutdown')

		
	def run(self) :
		global debuglevel
		print ('%s %s - Starting' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), self.name))
		while not self.exit:
			i, o, e = select.select([sys.stdin], [], [], self.seconds)
			if i:
				ch = sys.stdin.read(1)
				ignore = sys.stdin.read(1)
				print('Keyboard Input - %s' % ch.strip('\r\n'))
				if ch == 't': # Send Test packet(s)
					pub.sendMessage('SendTestPacket', arg1='TestPacket')	
				if ch == 'q': # Close Baker Down
					#intExitFlag = 1
					pub.sendMessage('Shutdown')
				if ch == 'd': # Debug Level
					debuglevel = debuglevel + 1
					if debuglevel == 4: debuglevel = 0
					print ("    debuglevel - %s" % debuglevel)
		print('%s %s - Terminating' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), self.name))
		return
		
	def close(self):
		self.exit = True
			
class thrdAPRSReadPackets( threading.Thread ) :

	def __init__(self, name, APRSConn):
		threading.Thread.__init__(self)
		self.name = name
		self.APRSConn = APRSConn
		self.exit = False
		pub.subscribe(self.close, 'Shutdown')

	def run(self) :
		print ('%s %s - Starting' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), self.name))
		self.thread_ident = threading.current_thread().ident
		
		try:		
		# Watch APRS Connection for incoming packets
			while APRSConn.connected and not self.exit:
				# Get next APRSPacket, process it, wait for next one
				rawAPRSPacket = self.APRSConn.sock_file.readline()
				if rawAPRSPacket:
					APRSPacket = libfap.fap_parseaprs(rawAPRSPacket, len(rawAPRSPacket), 0)
					# Convert an APRS Packet to a Baker Packet
					if APRSPacket and APRSPacket[0].orig_packet:
						BPkt = clsBakerPacket(APRSPacket)
						self.APRSConn.sock_file.flush()
						libfap.fap_free(APRSPacket)
		except KeyboardInterrupt:
			print ('\n%s - APRS-IS Server > Connection terminated from keyboard []\n' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
			self.exit = True
		finally:
			libfap.fap_cleanup()
			self.APRSConn.sock.shutdown(0)
			self.APRSConn.sock.close()
			print('%s %s - Terminating' % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), self.name))
			pub.sendMessage('ShutdownDB')	

	def close(self):
		self.exit = True		

class BakerCommon(object):

	@classmethod
	def epoch2iso8601time(cls, epochSeconds):
		try:
			if isinstance(epochSeconds, str):
				if len(epochSeconds) <> 10:
					return epochSeconds
				elif len(epochSeconds) == 10 and eval(epochSeconds)  :
					return  datetime.fromtimestamp(eval(epochSeconds)).strftime('%Y-%m-%d %H:%M:%S')
			else:
				print 'epochSeconds is not a string -', epochSeconds
				return 'non string'
		except Exception as error:
			return 'DB data is bad'
			
	@classmethod
	def iso86012epochtime(cls, iso8601String):
		try:
			if isinstance(iso8601String.encode('utf-8'), str) and len(iso8601String) == 19:
				return  str(int(time.mktime(time.strptime(iso8601String, '%Y-%m-%d %H:%M:%S'))))
			else:
				return iso8601String
		except Exception as error:
			print 'iso86012epochtime - ', traceback.print_exc()
			return 'error in date parameter'
		
############################
# Main Program
############################

if __name__ == '__main__':
	print ('\nBAKER - APRS-IS Messaging Server')
	print ('BAKER - BARC.APRS.Kelly KE7QHW(SK).Event.Reporting')
	print ('BAKER - 2015  - Brian - KG7AFQ - V0.1')
	print ('BAKER - BSD3  - Open Source Licensed')
	print ('\n(To Quit - type q <cr>)')

	# execution flags
	debuglevel = 1
	
	# Create Ques
	SendQ = {} #Thread to hold and process Baker sent messages until they have been fully processed. 

	# Hold Baker DB Connection and Functions
	iBakerDB = clsBakerDB()
	iBakerCmd = clsBakerCommand()
	
	# Open Connection to APRS Server and DB
	try:
		APRSConn = clsAPRSConnection() 
		if APRSConn.connected:	
			# Create threads
			tSndBkrPkts = thrdSendPacketQ('Baker SendQ',  5, SendQ) # Hold and process Baker Packets to be sent
			tReadKeyBoardChars = thrdKeyboardPollerChars('Keyboard Poller', 1) # Watch for keyboard input
			tAPRSReadPackets = thrdAPRSReadPackets('Read APRS Packets', APRSConn) # Read, validate and send Valid Baker Packets to q 
			# Start Threads
			tSndBkrPkts.start()
			tReadKeyBoardChars.start()
			tAPRSReadPackets.start()
	except Exception as error:
		print ('\nBaker - Unable to make APRS IS Connection \nBaker - Check the config in the file settings.py \nBaker - Terminating\n\n\n')
		if debuglevel > 1:
			traceback.print_exc() 
	finally:
		pass
					
###########################
### End
###########################
