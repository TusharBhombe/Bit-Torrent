import socket
from urllib.request import urlopen
from bencoding import bdecode,bencode
import hashlib
import time
from threading import Thread,Lock
from urllib.parse import urlencode
import random
import struct
import os
import math
import sys
PORT = 6882
def ip_from_hex(hexa):
	ip=""
	for i in hexa:
		ip+=str(i)+"."
	return ip[:-1]

def port_from_hex(hexa):
	return struct.unpack(">H",hexa)[0]



