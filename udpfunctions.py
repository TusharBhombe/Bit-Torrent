from commonutils import *

def get_address_for_udp(url):
	i=-1
	j=-1
	try:
		val=int(url[j])
		j=len(url)
	except:
		while(url[j]!='/'):
			j-=1
	
	while(url[i]!=':'):
		i-=1
	
	try:
		port=int(url[i+1:j])
		url=url[6:i]
	except:
		return (None,None)
	
	try:
		ip=socket.gethostbyname(url)
	except:
		ip=None

	return (ip,port)	#(ip_address, portNumber)

def get_udp_connection_request():
	protocol_id = 0x41727101980	#magical constant
	action = 0		#connect
	transaction_id = random.randint(1,1000)	#random transaction id
	conreq = bytes("", "utf-8")
	conreq += struct.pack("!q", protocol_id)
	conreq += struct.pack("!i", action)
	conreq += struct.pack("!i", transaction_id)
	return (conreq, transaction_id)

def extract_udp_connection_response(response):
	if(len(response)<16): return None,None,None
	action = struct.unpack_from("!i",response,0)[0]
	transaction_id = struct.unpack_from("!i",response,4)[0]
	connection_id = struct.unpack_from("!q",response,8)[0]
	return (action,transaction_id,connection_id)

def get_udp_announce_request(connection_id, transaction_id, infohash, peer_id):
	action=1
	downloaded = 0
	left = 0
	uploaded = 0
	event = 2
	IPA = 0
	key = random.randint(1,100)
	numwant = -1
	port =  6882
	annreq = bytes("","utf-8")
	annreq += struct.pack("!q",connection_id)
	annreq += struct.pack("!i",action)
	annreq += struct.pack("!i",transaction_id)
	annreq += struct.pack("!20s",infohash)
	annreq += struct.pack("!20s",bytes(peer_id,"utf-8"))
	annreq += struct.pack("!q",downloaded)
	annreq += struct.pack("!q",left)
	annreq += struct.pack("!q",uploaded)
	annreq += struct.pack("!i",event)
	annreq += struct.pack("!i",IPA)
	annreq += struct.pack("!i",key)
	annreq += struct.pack("!i",numwant)
	annreq += struct.pack("!h",port)
	return annreq

def extract_udp_announce_response(response):
	addresses=[]
	if(len(response)<20): return addresses
	action = struct.unpack_from("!i",response,0)[0]
	if(action!=1): return addresses
	transaction_id = struct.unpack_from("!i",response,4)[0]
	interval = struct.unpack_from("!i",response,8)[0]
	leechers = struct.unpack_from("!i",response,12)[0]
	seeders = struct.unpack_from("!i",response,16)[0]
	cur=26
	ln = len(response)
	while(cur <= ln):
		addresses.append(tuple([ip_from_hex(response[cur-6:cur-2]),port_from_hex(response[cur-2:cur])]))
		cur += 6
	return addresses
