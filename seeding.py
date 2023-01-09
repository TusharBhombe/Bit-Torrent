from commonutils import *

def extract_handshake_request(Handshake):
        len_id = struct.unpack_from("b",Handshake,0)[0]
        protocol_id = struct.unpack_from(f"!{len_id}s",Handshake,1)[0]
        reserved = struct.unpack_from("!8b",Handshake,len_id+1)
        infohash = Handshake[len_id+9:len_id+29]
        peer_id = struct.unpack_from("!20s",Handshake,len_id+29)[0]
        return protocol_id.decode(), infohash, peer_id.decode()

def generate_handshake_response(protocol_id,infohash,peer_id):
        len_id = len(protocol_id)
        handmsgR = bytes("",'utf-8')
        handmsgR += struct.pack("b",len_id)
        handmsgR += struct.pack(f"!{len_id}s",bytes(protocol_id,"utf-8"))
        for i in range(8):
                handmsgR += struct.pack("b",0)
        handmsgR += infohash
        handmsgR += struct.pack("!20s",bytes(peer_id,"utf-8"))
        return handmsgR

def create_chock():
        LEN = 1
        ID = 0
        chock = bytes("","utf-8")
        chock += struct.pack("!i",LEN)
        chock += struct.pack("!b",ID)
        return chock

def create_unchock():
        LEN = 1
        ID = 1
        unchock = bytes("","utf-8")
        unchock += struct.pack("!i",LEN)
        unchock += struct.pack("!b",ID)
        return unchock

def generate_block_request(index,begin,size):
	request = bytes("",'utf-8')
	request += struct.pack("!i",13)
	request += struct.pack("!b",6)
	request += struct.pack("!i",index)
	request += struct.pack("!i",begin)
	request += struct.pack("!i",size)
	return request

def extract_block_request(BlockRequest):
        LENGTH = struct.unpack_from("!i",BlockRequest,0)[0]
        ID = struct.unpack_from("!b",BlockRequest,4)[0]
        INDEX = struct.unpack_from("!i",BlockRequest,5)[0]
        BEGIN = struct.unpack_from("!i",BlockRequest,9)[0]
        SIZE = struct.unpack_from("!i",BlockRequest,13)[0]
        return INDEX,BEGIN,SIZE

def create_block(index,begin,data):
        length = len(data) + 9
        id = 7
        BLOCK =  struct.pack("!i", length)
        BLOCK += struct.pack("!b", id)
        BLOCK += struct.pack("!i", index)
        BLOCK += struct.pack("!i", begin)
        BLOCK += data
        return BLOCK

def IsInterested(message):
        lenght = struct.unpack_from("!i",message,0)[0]
        if(lenght!=1): return False
        ID = struct.unpack_from("!b",message,4)[0]
        if(ID!=2): return False
        return True        
