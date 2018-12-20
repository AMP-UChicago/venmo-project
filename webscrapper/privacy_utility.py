#Library used to protect privacy 
#As it currently stands the library seems super redudndant/not that elegant
# and I might just delete this later
import sys
import hashlib

# Be careful about what you enter into these functions, cryptographic functions are 
# one-way, meaning we cannot revert/figure out the original input through the output

#NOTE: UTF-8 ENCODING is the same as Byte Literal

#NOTE: WE MAY ALSO NEED TO SALT OUR HASHES

# List of guarenteed hasing algorithims in python3
# blake2b
# blake2s
# md5
# sha1
# sha224
# sha256
# sha384
# sha3_224
# sha3_256
# sha3_384
# sha3_512
# sha512
# shake_128
# shake_256

def crypto_hash(input_str: str, encoding='utf-8',algo='sha256'):
	hash_dict = {
		'blake2b':hashlib.blake2b,
		'blake2s':hashlib.blake2s, 
		'md5':hashlib.md5, 
		'sha1':hashlib.sha1,
		'sha224':hashlib.sha224,
		'sha256':hashlib.sha256,
		'sha384':hashlib.sha384,
		'sha3_224':hashlib.sha3_224,
		'sha3_256':hashlib.sha3_256,
		'sha3_384':hashlib.sha3_384,
		'sha3_512':hashlib.sha3_512,
		'sha512':hashlib.sha512
		# 'shake_128':hashlib.shake_128, #SHAKE algorithms need hexdigest(length)
		# 'shake_256':hashlib.shake_256  #And I don't wnat to deal with that
	}
	hash_f = hash_dict.get(algo,
				lambda: sys.exit('ERROR: Invalid Hashing Algorithm Chosen'))
	return hash_f(input_str.encode(encoding)).hexdigest()

#A pseudo hash salting function - it is not a perfect hash function, but it will
#obfsucate usernames/passwords MORE than just a plain cryptographic hash  
def salt_str(username: str, encoding='utf-8',algo='sha256'):
	pseudo_salt = crypto_hash(username, encoding=encoding, algo=algo)
	return username + pseudo_salt

def hash_username(username: str,encoding='utf-8',algo='sha256'):
	# This seems super redundant and not pythonic, so I might just delete this later
	return crypto_hash((salt_str(username)),encoding=encoding,algo=algo)

def unit_testing():
	pass
	return

if __name__ == '__main__':
	print("Do something here")
	# salt = (hashlib.sha256(b'abc')).hexdigest()
	# combined = 'abc' + salt
	# a = hashlib.sha256(combined.encode('utf-8'))
	# print(a.hexdigest())
	# print(hash_username('abc',encoding='utf-8'))
	# print(hash_username('abc',encoding='utf-16'))
	# print(hash_username('abc',encoding='utf-32'))
	# print(hash_username('abc',algo='sha512'))
	# print(hashlib.algorithms_available) 
	# print(hashlib.algorithms_guaranteed)

