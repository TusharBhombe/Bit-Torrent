from commonutils import * 

def extract_torrent(filename):
	with open(filename,"rb") as file:
		data = bdecode(file.read())
	return data

def getAllPiecesHash(HashString):
	pieces = len(HashString)
	HashDectionary = []
	j=0
	for i in range(0,pieces,20):
		HashDectionary.append(HashString[i:i+20])
		j+=1
	return HashDectionary

def get_Sha1Hash(data):
	return hashlib.sha1(data).digest()

def createDirectories(dirs):
	filename=""
	for dir in dirs:
		filename+=dir+"/"
		if(not os.path.exists(filename)):
			os.mkdir(filename)
	return
