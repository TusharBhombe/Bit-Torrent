#!user/bin/python3
from sys import argv
from commonutils import *
from peer import *
from seeding import *
from torrentfile import *
from httpfunctions import *
from udpfunctions import *
from seeding import *

class Main:
	def __init__(self,Speed,Peer):
		self.peer_id = "-DA2021-536723892673"
		self.lock = Lock()
		self.MAX_ALLOWED_PEER = Peer
		self.MAX_ALLOWED_SPEED = Speed
		self.tempPath=""
		return

	def run(self,filename):
		data = extract_torrent(filename)
		self.FileName = data[b'info'][b'name'].decode()
		self.all_participated_peers=0
		self.PieceLength = data[b'info'][b'piece length']
		self.InfoHash = get_Sha1Hash(bencode(data[b'info']))
		self.handshake_message = get_handshake_request(self.InfoHash,self.peer_id)
		self.interested = generate_interested()
		self.BlockSize = 2**14
		self.announce = data[b'announce'].decode()
		self.AllPeersBitfields = {}
		self.DownloadedPerPeer = {}
		self.PeerConnectedTime = {}
		self.Speeds={}
		self.Started = False
		self.OverAllDownloadSpeed = 0

		try:
			self.AnnounceList = data[b'announce-list']
		except:
			self.AnnounceList = None

		try:
			self.multifiles = data[b'info'][b'files']
		except:
			self.multifiles = False

		if(self.multifiles):
			self.all_files = {}	#storing all files path and length
			self.length=0
			for file in self.multifiles:
				self.length += file[b'length']
				pathd = [path.decode() for path in file[b'path']]
				createDirectories([self.FileName] + pathd[:-1])
				completePath = self.FileName
				for i in pathd:
					completePath += "/" + i
				self.all_files[completePath]=file[b'length']
			self.multifiles=True
			self.tempPath="temp"
		else:
			self.length=data[b'info'][b'length']

		self.AllPieceHashes = getAllPiecesHash(data[b'info'][b'pieces'])
		self.totalpieces = math.ceil(self.length/self.PieceLength)
		self.BitField = [0 for _ in range(self.totalpieces)]
		self.PiecesCount = [0 for _ in range(self.totalpieces)]
		self.lastPiece = self.length % self.PieceLength
		if(self.lastPiece==0):
			self.lastPiece = self.PieceLength

		th = Thread(target=self.startSeeding )
		th.start()
		th=Thread(target=self.downloadSpeed )
		th.start()
		th=Thread(target=self.screenStat )
		th.start()
		
		if('udp' in self.announce):
			self.udp_tracker_handler()
		else:
			self.http_tracker_handler()

		if(self.multifiles):
			return self.makeCorrectFiles()
		return

	"""
	-----------------------------------
	|	Tracker Functions         |
	-----------------------------------
	"""
	def udp_tracker_handler(self):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		connection_req, trans_id = get_udp_connection_request()
		announce = self.announce
		TIMEOUT = 1
		sock.settimeout(TIMEOUT)
		count = 0
		numbered = 0
		index=0
		address = get_address_for_udp(announce)
		all_working_trackers={}
		flag=1
		while((self.AnnounceList and numbered<len(self.AnnounceList)) or (not self.AnnounceList and flag)):
			try:
				sock.sendto(connection_req, address)
				connection_res, address = sock.recvfrom(2048)
				all_working_trackers[address] = connection_res
				count=100
			except:
				count+=1
				TIMEOUT = TIMEOUT*1.5

			if(count>=4):
				announce = self.AnnounceList[numbered][index].decode()
				index+=1
				if(index>=len(self.AnnounceList[numbered])):
					numbered+=1
					index=0
				address = get_address_for_udp(announce)
				flag=0
				count=0

		process=[]
		for address in all_working_trackers:
			connection_res=all_working_trackers[address]
			cr_action,cr_trans_id,connection_id = extract_udp_connection_response(connection_res)
			if(trans_id != cr_trans_id or cr_action!=0): continue
			announce_req = get_udp_announce_request(		#create announce request
						connection_id=connection_id,
						transaction_id=trans_id,
						infohash=self.InfoHash, 
						peer_id=self.peer_id
					)
			count=0
			flag=0
			while(count<3):
				try:
					sock.sendto(announce_req, address)
					announce_res, address = sock.recvfrom(2048)
					flag=1
					count=100
				except:
					count+=1

			#if got announce response
			if(flag):
				peers = extract_udp_announce_response(announce_res)
				for peer in peers:
					while(self.all_participated_peers >= self.MAX_ALLOWED_PEER):
						continue
					th = Thread(target=self.communicateWithPeer, args=(peer, ))
					th.start()
					process.append(th)
		for th in process:
			th.join()

		return

	def http_tracker_handler(self):
		request = get_http_tracker_request(
						URL=self.announce,
						infohash=self.InfoHash,
						peer_id=self.peer_id, 
						port=6881, 
						uploaded=0, 
						downloaded=0, 
						left=1000, 
						compact=1
					)
		response = urlopen(request)
		peers = extract_http_response(bdecode(response.read()))
		process=[]
		for peer in peers:
			while(self.all_participated_peers>=self.MAX_ALLOWED_PEER):
				continue
			th = Thread(target=self.communicateWithPeer, args=(peer, ))
			th.start
			process.append(th)
		if(not self.AnnounceList): return
		process=[]
		for ann in self.AnnounceList:
			for announce in ann:
				request = get_http_tracker_request(URL=announce.decode(), infohash=self.InfoHash ,peer_id=self.peer_id, port=6881, uploaded=0, downloaded=0, left=1000, compact=1)
				response = urlopen(request)
				peers = extract_http_response(bdecode(response.read()))				
				for peer in peers:
					while(self.all_participated_peers>=self.MAX_ALLOWED_PEER):
						continue
					th = Thread(target=self.communicateWithPeer, args=(peer, ))
					th.start()
					process.append(th)
		for i in process:
			i.join()
		return

	"""
	----------------------------------
	|     Peer Communications        |
	----------------------------------
	"""
	def communicateWithPeer(self,address):
		if(0 not in self.BitField ): return
		try:
			tcp_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			tcp_socket.settimeout(2)
			tcp_socket.connect(address)
		except:
			return 
		bitfield = self.makeHandshakeWithPeer(tcp_socket)
		if(bitfield==b'' or not bitfield):
			return

		if(self.isItUnChocking(tcp_socket)):
			if(self.all_participated_peers>=self.MAX_ALLOWED_PEER): return True
			self.DownloadedPerPeer[address[0]] = 0
			th=Thread(target=self.separatePeerDownloadSpeed, args=(address[0],))
			th.start()
			with self.lock:
				self.all_participated_peers+=1
			self.startDownloading(bitfield,tcp_socket,address[0])
		return True

	def makeHandshakeWithPeer(self,tcp_socket):
		tcp_socket.send(self.handshake_message)
		handshake_response = bytes("","utf-8")
		response = None
		while(True):
			try:
				response =tcp_socket.recv(5120)
			except:
				if(handshake_response):
					break
			if(response):
				handshake_response += response
			else:
				break
		return get_bitfield(handshake_response)

	def isItUnChocking(self,tcp_socket):
		CHOCK=0
		tcp_socket.settimeout(20)
		try:
			tcp_socket.send(self.interested)
			response = tcp_socket.recv(5120)
		except:
			#print("timeout")
			return False
		if(len(response) < 5): return False
		if(isChockOrUnchock(response) == CHOCK):
			return False
		return True

	"""
	-----------------------------
	|  Downloading Functions    |
	-----------------------------
	"""
	def findRearest(self,bitfield):
		with self.lock:
			indices = sorted(
				range(len(self.BitField)),
				key = lambda i: (self.BitField[i], self.PiecesCount[i],)
			)
			for index in indices:
				if(self.BitField[index]==0 and bitfield[index]=='1'):
					self.PiecesCount[index] += 1
					return True,index
			return False,-1

	def startDownloading(self,bitfield,tcp_socket,ip):
		while 0 in self.BitField:
			while(self.OverAllDownloadSpeed>=self.MAX_ALLOWED_SPEED):
				Time=0
				while(Time<60):
					Time+=1
					time.sleep(1)
				try:
					tcp_socket.send(keep_alive())
				except:
					tcp_socket.close()
					return

			status,index = self.findRearest(bitfield)
			if(not status):
				with self.lock:
					self.all_participated_peers-=1
				return
			self.download_piece(index,tcp_socket,self.BlockSize,ip)
		return

	def download_piece(self,index,tcp_socket,BlockSize,ip):
		self.Started=True
		piece = bytes("","utf-8")
		tcp_socket.settimeout(10)
		if(index != self.totalpieces-1):
			iterations = self.PieceLength//BlockSize
			length = self.PieceLength
		else:
			if(self.lastPiece < self.BlockSize):
				BlockSize = self.lastPiece
			iterations = math.ceil(self.lastPiece/BlockSize)
			length = self.lastPiece

		count = 0
		while(count < iterations):
			time.sleep(1)
			if(self.BitField[index]==1): return True
			br = generate_block_request(index,count*(BlockSize),min(BlockSize,length-count*BlockSize))
			tcp_socket.send(br)
			ans = bytes("","utf-8")
			while(len(ans)<length):
				if(self.BitField[index]==1): return True
				try:
					ans += tcp_socket.recv(BlockSize)
				except:
					if(ans):
						break
					continue

			block , correct = extract_block(ans,index)
			if(correct):
				piece+=block
				count += 1
		
		blockh = hashlib.sha1(piece).digest()
		self.DownloadedPerPeer[ip]+=1
		if(blockh!=self.AllPieceHashes[index]): return False	
		self.writePieceToFile(piece,index, self.tempPath + self.FileName)		
		return True

	"""
	-----------------------------------
	|	Writing to To File        |
	-----------------------------------
	"""
	def writePieceToFile(self,piece,index,filename):
		if(self.BitField[index] == 1):
			return True
		if(not os.path.exists(filename)):
			os.mknod(filename)
		if(self.BitField[index]==1):
			return True
		with self.lock:
			with open(filename,"r+b") as file:
				data = struct.pack("<" + "B" * len(piece),*piece)
				file.seek(index*self.PieceLength)
				file.write(data)
				file.flush()
				file.close()
			self.BitField[index]=1
		return True

	def writeFileToFile(self,src,dest,start,length,bufsize=2*20):
		with open(src, "rb") as f1:
			f1.seek(start)
			with open(dest, "wb") as f2:
				while length:
					part = min(bufsize, length)
					data = f1.read(part)
					f2.write(data)
					length-=part
		return True
	
	def makeCorrectFiles(self):
		start=0
		for file in self.all_files:
			self.writeFileToFile(self.tempPath+self.FileName,file,start, self.all_files[file])
			start += self.all_files[file]
		os.remove(self.tempPath+self.FileName)
		return True

	"""
	------------------------------------------
	|         USER INTERFACE FUNCTIONS       |
	------------------------------------------
	"""
	def separatePeerDownloadSpeed(self,ip):
		TIME=0
		while(True):
			time.sleep(1)
			TIME+=1
			self.Speeds[ip] = self.DownloadedPerPeer[ip]*self.PieceLength/TIME
			if(0 not in self.BitField):
				return

	def downloadSpeed(self):
		while(not self.Started): continue
		TIME=0
		while(True):
			time.sleep(1)
			TIME+=1
			self.OverAllDownloadSpeed = sum(self.BitField)*(self.PieceLength)/TIME
			if(0 not in self.BitField):
				return

	def screenStat(self):
		ln=len(self.BitField)
		while(True):
			time.sleep(1)
			os.system('clear')
			downloaded = math.ceil(sum(self.BitField)/ln*50)
			print("#"*downloaded+"."*(50-downloaded))
			print("Download Speed : ",self.OverAllDownloadSpeed)
			for ip in self.Speeds:
				print(f'{ip} : {self.Speeds[ip]}')
			print(f"Currently Donloading from {self.all_participated_peers} peers")
			if(0 not in self.BitField):
				os.system('clear')
				print("Download Complete....")
				return

	"""
	-----------------------------
	|     SEEDING FUNCTIONS      |
	----------------------------- 
	"""
	def create_Bitfield(self):
		Bstring = ""
		for i in self.BitField:
			Bstring += str(i)

		while(len(Bstring)%8):
			Bstring += '0'

		ln = len(Bstring)
		ID = 5
		BitField = int(Bstring,2).to_bytes((ln+7)//8,"big")
		LENGTH = len(BitField) + 1
		header = struct.pack("!ib",LENGTH,ID)
		BitField = header + BitField
		return BitField

	def seedToPeer(self,connection,address):
		try:
			connection.settimeout(60)
			handshake_request = connection.recv(1024)
			protocol_id, infohash, peer_id = extract_handshake_request(handshake_request)
		except:
			connection.close()
			return
		response = generate_handshake_response(protocol_id,infohash,peer_id)
		bitfield = self.create_Bitfield()
		connection.send(response)
		connection.send(bitfield)
		while 0 in self.BitField:
			try:
				connection.settimeout(60)
				message = connection.recv(1024)
			except:
				connection.close()
				break
			if(not IsInterested(message)):
				continue
			connection.send(create_unchock())
			while 0 in self.BitField:
				try:
					connection.settimeout(30)
					blockRequest = connection.recv(1024)
				except Exception as e:
					break
				if(not blockRequest or blockRequest==b''):
					time.sleep(5)
					continue
				INDEX,BEGIN,SIZE = extract_block_request(blockRequest)
				if(self.BitField[INDEX]==0):
					continue
				with self.lock:
					file = open(self.tempPath + self.FileName, "r+b")
					file.seek((INDEX * self.PieceLength)+BEGIN)
					data = file.read(SIZE)
					file.close()
				BLOCK = create_block(INDEX,BEGIN,data)
				connection.send(BLOCK)
				time.sleep(5)
		return

	def startSeeding(self):
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server.bind(("", PORT))
		server.listen(50)
		self.peersForSeeding = {}
		processes=[]
		while 0 in self.BitField:
			connection, address = server.accept()
			th = Thread(target = self.seedToPeer, args=(connection, address))
			th.start()
			processes.append(th)



MAX_ALLOWED_SPEED = 100000	#default
MAX_ALLOWED_PEER = 50		#default

try:
	filename = sys.argv[1]
except:
	print("Please Enter torrentfile")
	print("correct format is ' filename -s  Max_Allowed_Speed -p Max_Allowed_Peers '")
	sys.exit(0)

ln = len(sys.argv)
index = 2
while(index<ln):
	if(sys.argv[index]=='-s'):
		flag=1
		try:
			MAX_ALLOWED_SPEED = float(sys.argv[index+1]) * 1000
		except:
			print("Please Enter Speed! in kb")
			print("correct format is ' filename -s  Max_Allowed_Speed -p Max_Allowed_Peers '")
			sys.exit(0)
			
	elif(sys.argv[index]=="-p"):
		flag=1
		try:
			MAX_ALLOWED_PEER = int(sys.argv[index+1])
		except:
			print("Please Enter Peers count!")
			print("correct format is ' filename -s  Max_Allowed_Speed -p Max_Allowed_Peers '")
			sys.exit(0)

		
	index+=1


cl = Main(MAX_ALLOWED_SPEED,MAX_ALLOWED_PEER)
cl.run(filename)



