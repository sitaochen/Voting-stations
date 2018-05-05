import socket
import time
import random
import sys
import json

TCP_IP = "127.0.0.1"

TCP_PORT1 = 5005 # serverA
TCP_PORT2 = 5006 # serverB
TCP_PORT3 = 5007 # serverC

while True:
	print("")
	request = input("How can I help you today? (Vote, printDict, printLog or printTable)\n")
	if request == "quit":
		print("No more request.")
		break

	if request == "Vote,A" or request == "Vote,B":
		input_list = request.split(',')
		msg = input_list[1]
	elif request == "printDict" or request == "printLog" or request == "printTable":
		msg = request
	else:
		print("Error command, try again please.")
		continue

	print("Message received from the voter.")
	num = input("Which server do you want to connect? (A, B or C)\n")
	if num == "A":
		addr = (TCP_IP, TCP_PORT1)
		a = 'serverA'
	elif num == "B":
		addr = (TCP_IP, TCP_PORT2)
		a = 'serverB'
	else:
		addr = (TCP_IP, TCP_PORT3)
		a = 'serverC'

	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(addr)
		time.sleep(2)
	except:
		sock.close()
		print("Failed to send, " + a + " is down. Try again.")
		continue

	print("Message sent to " + a +".")
	sock.sendall(msg.encode('utf-8') + ','.encode('utf-8') + str(sys.argv[1]).encode('utf-8'))


	response = sock.recv(1024)
	time.sleep(1)
	if request == "Vote,A" or request == "Vote,B":
		print(response.decode('utf-8'))
	else:
		# log table dictionary
		b = b''
		b += response
		d = json.loads(b.decode('utf-8'))
		print(d)

	sock.close()
