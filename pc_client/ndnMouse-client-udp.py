#!/usr/bin/env python3

import sys, time
import socket, ipaddress
import pyautogui

import logging
import pickle

from Crypto import Random
from Crypto.Cipher import AES
import hashlib

def main(argv):
	LOG_FILENAME = "log.txt"
	logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
	
	default_address = '149.142.48.182'
	default_port = 10888

	# Prompt user for server address
	server_address = getServerAddress(default_address)
	#server_port = getSeverPort(default_port)	# Just leaving at default for now...

	# Prompt user for password
	password = getPassword()

	# Create server and run it
	if not password:
		server = ndnMouseClientUDP(server_address, default_port)
	else:
		server = ndnMouseClientUDPSecure(server_address, default_port, password)
	
	try:
		server.run()
	except KeyboardInterrupt:
		print("\nExiting...")
		logging.info("Exiting...")
	finally:
		server.shutdown()

################################################################################
# Class ndnMouseClientUDP
################################################################################

class ndnMouseClientUDP():
	
	# pyautogui variables
	transition_time = 0
	pyautogui.FAILSAFE = False
	pyautogui.PAUSE = 0

	packet_bytes = 16
	max_refresh_attempts = 3
	

	def __init__(self, addr, port):
		self.server_address = (addr, port)
		self.bind_address = ('', port)
		self.refresh_attempts = 0


	# Establish connection with server
	def _openConnection(self):		
		got_timeout = True
		while got_timeout:
			message = b"OPEN"
			logging.info(b"Sending message: " + message)
			try:
				self.sock.sendto(message, self.server_address)
				msg, server = self.sock.recvfrom(self.packet_bytes)
				logging.info("Received message: {0}".format(msg))

				if msg.startswith(b"OPEN-ACK"):
					got_timeout = False
					# Reset refresh attempts (so we go back to heartbeat)
					self.refresh_attempts = 0
					logging.info("Connected to server {0}:{1}.".format(*server))

			except socket.timeout:
				continue


	# Send messge to refresh the connection (heartbeat)
	def _refreshConnection(self):
		got_timeout = True
		while got_timeout:
			message = b"HEART"
			logging.info("Sending message: {0}".format(message))
			try:
				self.sock.sendto(message, self.server_address)
				msg, server = self.sock.recvfrom(self.packet_bytes)
				logging.info("Received message: {0}".format(msg))

				if msg.startswith(b"BEAT"):
					got_timeout = False
					# Reset refresh attempts
					self.refresh_attempts = 0
					logging.info("Connected to server {0}:{1}.".format(*server))

			except socket.timeout:
				# Keep track of refresh timeouts and try again
				self.refresh_attempts += 1
				if self.refresh_attempts >= self.max_refresh_attempts:
					return


	# Run the server
	def run(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(self.bind_address)
		self.sock.settimeout(1.0)

		print("Use ctrl+c quit at anytime....")
		print("Listening to {0}, port {1}.".format(*self.server_address))
		logging.info("Use ctrl+c quit at anytime....")
		logging.info("Listening to {0}, port {1}.".format(*self.server_address))

		self._openConnection()
				
		# Receive and process mouse updates forever
		while True:
			try:
				msg, server = self.sock.recvfrom(self.packet_bytes)
			except socket.timeout:
				if self.refresh_attempts < self.max_refresh_attempts:
					self._refreshConnection()
				else:
					self._openConnection()
				continue

			logging.info("Received message: {0}".format(msg))
			
			# Handle different commands
			if msg.startswith(b"M") or msg.startswith(b"A"):
				self._handleMove(msg)
			elif msg.startswith(b"S"):
				self._handleScroll(msg)
			elif msg.startswith(b"C"):
				_, click, updown = msg.decode().split('_')
				self._handleClick(click, updown)
			elif msg.startswith(b"K"):
				_, keypress, updown = msg.decode().split('_')
				self._handleKeypress(keypress, updown)
			else:
				logging.error("Bad command received. Password on server?")


	# Shutdown the server
	def shutdown(self):
		message = b"CLOSE"
		logging.info(b"Sending message: " + message)
		self.sock.sendto(message, self.server_address)
		self.sock.close()


	############################################################################
	# Handle Mouse Functions
	############################################################################

	# Handle click commands
	def _handleClick(self, click, updown):
		if updown == "U":  	# UP
			pyautogui.mouseUp(button=click)
		elif updown == "D":	# DOWN
			pyautogui.mouseDown(button=click)
		elif updown == "F":	# FULL
			pyautogui.click(button=click)
		else:
			logging.error("Invalid click type: {0} {1}".format(click, updown))

	# Handle keypress commands
	def _handleKeypress(self, keypress, updown):
		if updown == "U":	# UP
			pyautogui.keyUp(keypress)
		elif updown == "D":	# DOWN
			pyautogui.keyDown(keypress)
		elif updown == "F":	# FULL
			pyautogui.press(keypress)
		else:
			logging.error("Invalid keypress type: {0} {1}".format(keypress, updown))


	# Handle movement commands
	# Format of commands:  M<x-4B><y-4B>
	#	b"A\x00\x00\x01\x90\x00\x00\x01\xf4"	(move to absolute pixel coordinate x=400, y=500)
	#	b"M\xff\xff\xff\xb5\x00\x00\x00\x19"	(move 75 left, 25 up relative to current pixel position)
	def _handleMove(self, data):
		move_type = data[:1]
		x = intFromBytes(data[1:5])
		y = intFromBytes(data[5:9])

		# Move mouse according to move_type (relative or absolute)
		if (move_type == b"M"):
			pyautogui.moveRel(x, y, self.transition_time)
		elif (move_type == b"A"):
			pyautogui.moveTo(x, y, self.transition_time)

	# Handle two-finger scroll commands
	# Format of commands:  S<y-4B>
	#   b"S\x00\x00\x00\x19"	(scroll 25 up)
	def _handleScroll(self, data):
		move_type = data[:1]
		x = intFromBytes(data[1:5])
		y = intFromBytes(data[5:9])
		# Prevent bug with pyautogui library where x < 10 causes opposite horizontal scrolling behavior
		# https://github.com/asweigart/pyautogui/issues/154
		if not (-9 <= x and x <= -1):
			pyautogui.hscroll(x)
		if y:
			pyautogui.vscroll(y)


################################################################################
# Class ndnMouseClientUDPSecure
################################################################################

# Packet description
#                     1                   2                   3    
# 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 
# -----------------------------------------------------------------
# |              IV               |  Seq  |  Message (PKCS5 pad)  |
# -----------------------------------------------------------------
# <~~~~~~~~~ plaintext ~~~~~~~~~~~><~~~~~~~~~ ciphertext ~~~~~~~~~>

class ndnMouseClientUDPSecure(ndnMouseClientUDP):
	
	# Constants
	seq_num_bytes = 4
	iv_bytes = 16
	key_bytes = 16
	aes_block_size = 16
	packet_bytes = 32
	max_seq_num = 2147483647


	def __init__(self, addr, port, password):
		super().__init__(addr, port)
		self.password = password
		self.key = b""	# To be set when we generate a password salt in _openConnection
		self.open_key = self._getKeyFromPassword(password)
		self.rndfile = Random.new()


	# Establish connection with server
	def _openConnection(self):
		got_timeout = True
		while got_timeout:
			self.seq_num = 0
			iv = self._getNewIV()
			self.key = self._getKeyFromPassword(self.password, salt=iv)

			# Create message from IV, seq num, and protocol msg
			message = intToBytes(self.seq_num) + b"OPEN"
			logging.debug(b"Sending message: " + iv + message)
			encrypted_message = self._encryptData(message, self.open_key, iv)
			encrypted_message_with_iv = iv + encrypted_message
			try:
				# Send and receive data
				self.sock.sendto(encrypted_message_with_iv, self.server_address)
				data, server = self.sock.recvfrom(self.packet_bytes)

				# Extract cleartext IV and ciphertext response, then decrypt it
				server_iv = data[:self.iv_bytes]
				encrypted = data[self.iv_bytes:]
				decrypted = self._decryptData(encrypted, self.key, server_iv)

				# If decrypted response is what we expect...
				if decrypted.startswith(b"\x00\x00\x00\x01OPEN-ACK"):
					# Incrememt the seq num (for this case it will always be 1)
					self.seq_num = 1
					# Reset refresh attempts (so we go back to heartbeat)
					self.refresh_attempts = 0
					# Break out of the loop
					got_timeout = False
					logging.info("Connected to server {0}:{1}.".format(*server))

			except socket.timeout:
				# No response, try again
				continue


	# Send messge to refresh the connection (heartbeat)
	def _refreshConnection(self):
		got_timeout = True
		while got_timeout:
			# Always increment seq num before sending any message (except opener msg)
			self.seq_num = self._getNextSeqNum()
			iv = self._getNewIV()
			
			# Create message from IV, seq num, and protocol msg
			message = intToBytes(self.seq_num) + b"HEART"
			logging.debug(b"Sending message: " + iv + message)
			encrypted_message = self._encryptData(message, self.key, iv)
			encrypted_message_with_iv = iv + encrypted_message
			try:
				# Send and receive data
				self.sock.sendto(encrypted_message_with_iv, self.server_address)
				data, server = self.sock.recvfrom(self.packet_bytes)

				# Extract cleartext IV and ciphertext response, then decrypt it
				server_iv = data[:self.iv_bytes]
				encrypted = data[self.iv_bytes:]
				decrypted = self._decryptData(encrypted, self.key, server_iv)

				server_seq_num = intFromBytes(decrypted[:self.seq_num_bytes])
				# logging.info("server seq num = {0}, client seq num = {1}".format(server_seq_num, self.seq_num))
				# If decrypted response has a valid seq num, and has the correct response...
				if (server_seq_num > self.seq_num or self.seq_num == self.max_seq_num) and decrypted[self.seq_num_bytes:].startswith(b"BEAT"):
					# Update our seq num to synchronize with server
					self.seq_num = server_seq_num
					# Reset refresh attempts
					self.refresh_attempts = 0
					# Break out of the loop
					got_timeout = False
					logging.info("Connected to server {0}:{1}.".format(*server))

			except socket.timeout:
				logging.info("Refresh Timeout!")
				# Keep track of refresh timeouts and try again
				self.refresh_attempts += 1
				if self.refresh_attempts >= self.max_refresh_attempts:
					return


	# Run the server
	def run(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(self.bind_address)
		self.sock.settimeout(1.0)

		print("Use ctrl+c quit at anytime....")
		print("Listening to {0}, port {1}.".format(*self.server_address))
		logging.info("Use ctrl+c quit at anytime....")
		logging.info("Listening to {0}, port {1}.".format(*self.server_address))

		self._openConnection()
				
		# Receive and process mouse updates forever
		while True:
			try:
				data, server = self.sock.recvfrom(self.packet_bytes)
			except socket.timeout:
				if self.refresh_attempts < self.max_refresh_attempts:
					self._refreshConnection()
				else:
					self._openConnection()
				continue

			logging.debug("Received from server {0}:{1}: {2}".format(server[0], server[1], data))

			# Extract cleartext IV and ciphertext message, then decrypt it
			server_iv = data[:self.iv_bytes]
			encrypted = data[self.iv_bytes:]
			decrypted = self._decryptData(encrypted, self.key, server_iv)

			server_seq_num = intFromBytes(decrypted[:self.seq_num_bytes])
			# If decrypted message has a valid seq num...
			if server_seq_num > self.seq_num or self.seq_num == self.max_seq_num:
				self.seq_num = server_seq_num
				msg = decrypted[self.seq_num_bytes:]
			
				# Handle different commands
				if msg.startswith(b"M") or msg.startswith(b"A"):
					self._handleMove(msg)
				elif msg.startswith(b"C"):
					_, click, updown = msg.decode().split('_')
					self._handleClick(click, updown)
				elif msg.startswith(b"K"):
					_, keypress, updown = msg.decode().split('_')
					self._handleKeypress(keypress, updown)
				else:
					logging.error("Bad command received. Wrong password?")


	# Shutdown the server
	def shutdown(self):
		self.seq_num = self._getNextSeqNum()
		iv = self._getNewIV()

		message = intToBytes(self.seq_num) + b"CLOSE"
		logging.debug(b"Sending message: " + message)
		encrypted_message = self._encryptData(message, self.key, iv)
		encrypted_message_with_iv = iv + encrypted_message

		self.sock.sendto(encrypted_message_with_iv, self.server_address)
		self.sock.close()


	############################################################################
	# Encryption Helpers
	############################################################################

	# Encrypt data
	def _encryptData(self, message, key, iv):
		logging.info(b"Data SENT: " + message)
		cipher = AES.new(key, AES.MODE_CBC, iv)
		message = self._PKCS5Pad(message, self.packet_bytes - self.iv_bytes)
		encrypted = cipher.encrypt(message)
		logging.debug(b"Encrypting data SENT: " + encrypted)
		return encrypted

	# Decrypt data
	def _decryptData(self, encrypted, key, iv):
		logging.debug(b"Encrypted data RECEIVED: " + encrypted)
		cipher = AES.new(key, AES.MODE_CBC, iv)
		decrypted = self._PKCS5Unpad(cipher.decrypt(encrypted))
		logging.info(b"Data RECEIVED: " + decrypted)
		return decrypted

	# Get a new random initialization vector (IV)
	def _getNewIV(self):		
		return self.rndfile.read(self.iv_bytes)

	# Get next unused seq num; handle if overflow occurs
	def _getNextSeqNum(self):
		if self.seq_num == self.max_seq_num:
			return 0
		else:
			return self.seq_num + 1

	# Hash password and salt (if provided) into key
	# 	password: string
	#	salt: byte string
	def _getKeyFromPassword(self, password, salt=b""):
		sha = hashlib.sha256()
		sha.update(password.encode() + salt)
		# Only take first 128 bits (16 B)
		return sha.digest()[:self.key_bytes]

	# PKCS5Padding padder, allows for longer than 16 byte pads by specifying maxPad
	def _PKCS5Pad(self, s, maxPad=aes_block_size):
		return s + (maxPad - len(s) % maxPad) * chr(maxPad - len(s) % maxPad).encode()

	# PKCS5Padding unpadder
	def _PKCS5Unpad(self, s):
		return s[0:-ord(chr(s[-1]))]


################################################################################
# User Input Functions
################################################################################

# Prompt user for server address and port, and validate
def getServerAddress(default_addr):
	last_ip_addr = "temp_ndnMouse.pkl"

	# Try to get pickle of last IP address
	try:
		with open(last_ip_addr, 'rb') as fp:
			last_addr = pickle.load(fp)
	except IOError:
		last_addr = default_addr
	
	addr = pyautogui.prompt(text="Enter server IP address", title="Server Address", default=last_addr)
	
	# Validate address
	try:
		ipaddress.ip_address(addr)
	except ValueError:
		pyautogui.alert(text="Address \"{0}\" is not valid!".format(addr), title="Invalid Address", button='Exit')
		sys.exit(1)

	# Save the last used IP address to pickle file
	with open(last_ip_addr, 'wb') as fp:
		pickle.dump(addr, fp)

	return addr


# Prompt user for server port, and validate
def getSeverPort(default_port):
	port_string = pyautogui.prompt(text="Enter server port number", title="Server Port", default=default_port)

	# Validate port
	try:
		port = int(port_string)
		if port < 1 or port > 65535:
			raise ValueError
	except ValueError:
		pyautogui.alert(text="Port \"{0}\" is not valid! Please enter a port between 1-65535.".format(port_string), title="Invalid Port", button='Exit')
		sys.exit(1)

	return port


# Prompt user for password, and validate it
def getPassword():
	password = pyautogui.password(text="Enter the server's password", title="Password", mask='*')
	# if not password:
	# 	pyautogui.alert(text="Password should not be empty!", title="Invalid Password", button='Exit')
	# 	sys.exit(1)

	return password

################################################################################
# Helper Functions
################################################################################

# Takes signed integer and tranforms to byte string (truncating if necessary)
def intToBytes(x):
	try:
		return x.to_bytes(4, 'big', signed=True)
	except OverflowError:
		x %= 2147483648
		return x.to_bytes(4, 'big', signed=True)

# Takes byte string and transforms to signed integer
def intFromBytes(xbytes):
	return int.from_bytes(xbytes, 'big', signed=True)


# Strip off script name in arg list
if __name__ == "__main__":
	main(sys.argv[1:])