from commonutils import *
def get_handshake_request(infohash,peer_id):
	protocol_id = "BitTorrent protocol"
	len_id = len(protocol_id)
	handmsg = bytes("",'utf-8')
	handmsg += struct.pack("b",len_id)
	handmsg += protocol_id.encode()
	for i in range(8):
		handmsg += struct.pack("b",0)
	handmsg += infohash
	handmsg += struct.pack("!20s",bytes(peer_id,"utf-8"))
	return handmsg


def getHaveIndices(HaveMessages):
	ln=len(HaveMessages)
	if(ln<9): return None
	allHavesIndex=[]
	start=0
	for i in range(9,ln+1,9):
		message=HaveMessages[start:i]
		start=i
		lenght = struct.unpack_from("!i",message,0)[0]
		id = struct.unpack_from("!b",message,4)[0]
		if(lenght!=5 or id!=4):
			continue
		index=struct.unpack_from("!i",message,5)[0]
		allHavesIndex.append(index)
	return allHavesIndex

def get_bitfield(handshake):
	buffer = handshake[68:]
	if(not buffer): return None
	bitfield_lenght= struct.unpack_from("!i",buffer,0)[0]
	if(buffer[4] != 5):
		return None
	bitfield = buffer[5:5+bitfield_lenght-1].hex()
	BitField = str(bin(int(bitfield,16))[2:])
	Haves=None
	notofuse = bitfield_lenght%8
	f=-1
	for i in range(notofuse):
		if(handshake[f]=='1'):
			return None
		f-=1
	try:
		HaveMessages = buffer[5+bitfield_lenght-1:]
		Haves = getHaveIndices(HaveMessages)
		for j in Haves:
			BitField=BitField[:j]+"1"+BitField[j+1:]
	except:
		pass
	return BitField

def generate_interested():
	interested = bytes("","utf-8")
	interested += struct.pack("!i",1)	#lenght 1
	interested += struct.pack("b",2)	# id 2
	return interested

def isChockOrUnchock(response):
	len = struct.unpack_from("!i",response,0)[0]
	res = struct.unpack_from("!b",response,4)[0]
	return res

def generate_block_request(index,begin,size):
	request = bytes("",'utf-8')
	request += struct.pack("!i",13)
	request += struct.pack("!b",6)
	request += struct.pack("!i",index)
	request += struct.pack("!i",begin)
	request += struct.pack("!i",size)
	return request

def extract_block(block_message,wantedindex):
	if(len(block_message)<13): return None,False
	length_pre = struct.unpack_from("!i",block_message)[0]
	id = struct.unpack_from("!b",block_message,4)[0]
	index = struct.unpack_from("!i",block_message,5)[0]
	if(wantedindex!=index or id!=7): return None,False
	begin = struct.unpack_from("!i",block_message,9)[0]
	block = block_message[13:]
	return block,True


def keep_alive():
	message = bytes("","utf-8")
	message += struct.pack("!i",0)
	return message