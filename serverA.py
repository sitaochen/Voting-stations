import socket
import time
import json
import pickle
import threading
from multiprocessing import Process, Lock
from threading import Thread
import os


mutex = Lock()

TCP_IP = "127.0.0.1"
TCP_PORT = 5005

SER2_IP = "127.0.0.1"
SER2_PORT = 5006

sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock1.bind((TCP_IP, TCP_PORT))

dictA = {"A" : 0, "B" : 0}
logA = []
tableA = [[0,0,0], [0,0,0], [0,0,0]]

order = 0

link = True

log_already = []

def writeFile():
	big_data = [dictA, logA, tableA, order, log_already, link]
	with open('serverA.txt', 'wb') as fp:
		pickle.dump(big_data, fp)
	fp.close()

def readFile():
	global dictA
	global logA
	global tableA
	global order
	global log_already
	global link
	try:
		with open('serverA.txt', 'rb') as fp:
			big_data = pickle.load(fp)
			dictA = big_data[0]
			logA = big_data[1]
			tableA = big_data[2]
			order = big_data[3]
			log_already = big_data[4]
			link = big_data[5]
			fp.close()
			os.remove("serverA.txt")
	except:
		pass

def getInput():
	global link
	while 1:
		request = input("Press 1 for link failure, 2 to bring back link and 3 for server failure.\n")
		if request == "1":
			print("Link from serverA -> serverB is down.")
			link = False
		elif request == "2":
			print("Link from serverA -> serverB is recovered.")
			link = True
		elif request == "3":
			print("ServerA is down.")
			writeFile()
			stream.close()
			os._exit(0)
		
class pack:
	def __init__(self, local_order, site, candidate):
		self.local_order = local_order
		self.site = site
		self.candidate = candidate

	def __eq__(self, other):
		if self.local_order == other.local_order:
			if self.site == other.site:
				return self.candidate == other.candidate
		return False

class deserialize(object):
	def __init__(self, j):
		self.__dict__ = json.loads(j)

	def __eq__(self, other):
		if self.local_order == other.local_order:
			if self.site == other.site:
				return self.candidate == other.candidate
		return False

class VoterThread(threading.Thread):
	def __init__(self, ip, port, conn):
		threading.Thread.__init__(self)
		self.ip = ip
		self.port = port
		self.conn = conn

	def run(self):
		data = (self.conn).recv(1024)
		print('Received data: ', data)
		# mutex.acquire()
		if len(data) <= 20:
			tmp = data.split((',').encode('utf-8'))
			command = tmp[0].decode('utf-8')
			if command == "A" or command == "B":
				UpdateVotes(command)
				(self.conn).sendall(("Vote received!").encode('utf-8'))
			elif command == "printDict":
				printDict(self.conn)
			elif command == "printLog":
				printLog(self.conn)
			elif command == "printTable":
				printTable(self.conn)
			self.conn.close()
		else:
			b = b''
			b += data
			msg_recv = json.loads(b.decode('utf-8'))
			log = msg_recv[0]
			log_deserialize = []
			for i in log:
				log_deserialize.append(deserialize(i))
			receiveAndUpdate(log_deserialize, msg_recv[1])
			gc()
		# mutex.release()

def printDict(conn):
	msg = json.dumps(dictA).encode('utf-8')
	conn.sendall(msg)

def printLog(conn):
	log_tmp = []
	for i in range (0, len(logA)):
		log_tmp.append(logA[i].candidate)
	msg = json.dumps(log_tmp).encode('utf-8')
	conn.sendall(msg)

def printTable(conn):
	msg = json.dumps(tableA).encode('utf-8')
	conn.sendall(msg)

def sendMessage():
	threading.Timer(3.0, sendMessage).start()
	global link
	mutex.acquire()
	if link == True:
		mutex.release()
		while 1:
			try:
				mutex.acquire()
				sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock2.connect((SER2_IP,SER2_PORT))
				break
			except:
				print("Trying to send message but serverB is down.")
				sock2.close()
				mutex.release()
			time.sleep(10)
		logA_serialize = []
		for i in range (0, len(logA)):
			element = logA[i]
			element = json.dumps(element.__dict__)
			logA_serialize.append(element)
		big_data = [logA_serialize, tableA]
		msg = json.dumps(big_data).encode('utf-8')
		sock2.sendall(msg)
		sock2.close()
	mutex.release()

def receiveAndUpdate(log, table):
	global log_already
	for i in range (1,3):
		tableA[i][0] = max(table[i][0], tableA[i][0])
		tableA[i][1] = max(table[i][1], tableA[i][1])
		tableA[i][2] = max(table[i][2], tableA[i][2])
	for i in range (3):
		tableA[0][i] = max(table[2][i], tableA[0][i])

	for i in range(len(log)):
		if log[i] not in log_already:
			logA.append(log[i])
			log_already.append(log[i])
			if log[i].candidate == "A":
				UpdateDict("A")
			else:
				UpdateDict("B")

def UpdateVotes(data):
	global order
	order += 1
	if data == "A":
		event = pack(order, "A", "A")
		UpdateDict("A")
	else:
		event = pack(order, "A", "B")
		UpdateDict("B")
	logA.append(event)
	tableA[0][0] = tableA[0][0] + 1

def UpdateDict(data):
	mutex.acquire()
	dictA[data] = dictA[data] + 1
	mutex.release()

### gc ###

def findAndDeleteEvent(log, numList, siteID):
	toBeDelete = []
	for i in range (len(log)):
		if log[i].local_order in numList and log[i].site == siteID:
			toBeDelete.append(i)
	log[:] = [a for b, a in enumerate(log) if b not in toBeDelete]

def gc():
	mini1 = min(tableA[0][0], tableA[1][0], tableA[2][0])
	if mini1 > 0:
		findAndDeleteEvent(logA, list(range(1, mini1 + 1)), "A")

	mini2 = min(tableA[0][1], tableA[1][1], tableA[2][1])
	if mini2 > 0:
		findAndDeleteEvent(logA, list(range(1, mini2 + 1)), "B")

	mini3 = min(tableA[0][2], tableA[1][2], tableA[2][2])
	if mini3 > 0:
		findAndDeleteEvent(logA, list(range(1, mini3 + 1)), "C")

### gc end ###

sock1.listen(1)
time.sleep(3)
readFile()
sendMessage()

linkFail = Thread(target = getInput)
linkFail.start()

while 1:
	(stream, (ip,port)) = sock1.accept()
	newthread = VoterThread(ip, port, stream)
	newthread.run()

stream.close()
