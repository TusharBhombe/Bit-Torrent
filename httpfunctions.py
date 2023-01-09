from commonutils import *

def get_http_tracker_request(URL,infohash,peer_id,port,uploaded,downloaded,left,compact):
	d = {"info_hash" : infohash,
		"peer_id" : peer_id,
		"port" : port,
		"uploaded" : uploaded,
		"downloaded" : downloaded,
		"left" : left,
		"compact" : compact }
	return URL + "?" + urlencode(d)

def extract_http_response(response):
	if (b'failure session' in response): return None
	interval = response[b'interval']
	peers = response[b'peers']
	ln = len(peers)
	addresses=[]
	for i in range(6,ln,6):
		addresses.append(tuple([ip_from_hex(peers[i-6:i-2]),port_from_hex(peers[i-2:i])]))
	return addresses
