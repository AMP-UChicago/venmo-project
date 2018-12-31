import sys
import hashlib

#NOTE: UTF-8 ENCODING is the same as Byte Literal
#Be careful about what you enter into these functions
#Cryptographic functions are one-way -
# meaning we cannot revert/figure out the original input through the output

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

# This seems super redundant and not pythonic, so I might just delete this later
def hash_username(username: str,encoding='utf-8',algo='sha256'):
	return crypto_hash((salt_str(username)),encoding=encoding,algo=algo)

#Really ugly, and needs fixing
def unit_test(param_fname:str,reference_fname:str,verbose=0):
	param_f = open(param_fname,"r")
	thashing_algos, tencoding_set, tstring_set = [],[],[]
	mode = 0 #1 for hashing_algo, 2 for encoding set, 3 for tstring_set
	num_algos, num_enset, num_tstrings = 0,0,0

	for line in param_f:
		cleaned = line.strip()
		#This method is sorta ugly and not very elegant, maybe implement a 
		#cleaner solution with dictionaries later 
		if(cleaned == "#TERMINATE"):
			break

		if(cleaned == "#HASHING ALGORITHMS"):
			mode = 1
			continue
		if(cleaned == "#ENCODING SETS"):
			mode = 2
			continue
		if(cleaned == "#TESTSTRINGS"):
			mode = 3
			continue

		if(mode == 1):
			thashing_algos.append(cleaned)
			num_algos += 1

		if(mode == 2):
			tencoding_set.append(cleaned)
			num_enset += 1

		if(mode == 3): 
			tstring_set.append(cleaned)
			num_tstrings += 1

	param_f.close()

	total_tests_num = num_algos * num_enset * num_tstrings

	refer_f = open(reference_fname)
	refer_f.seek(0,0) #reset to the beginning of the file
	
	correct,total = 0,0
	for x in thashing_algos:
		for y in tencoding_set: 
			for z in tstring_set:
				total += 1
				reference_line = (refer_f.readline()).strip()
				testoutput = "Testing: ({} ; {} ; {}) = {}".format(z,y,
								x,hash_username(z,encoding=y,algo=x))
				if(testoutput == reference_line): 
					correct += 1
				else: 
					if(verbose):
						print("THERE IS A MISMATCH IN THE HASHES BELOW")

				if(verbose): 
					print("(Reference Output) {}".format(reference_line))
					print("(Calculated Output) {}".format(testoutput))

	refer_f.close()

	if(total != total_tests_num):
		print("\nThe number of test cases DO NOT seem to match up")
	else:
		print("\nThe number of tests and actual cases match up!")

	print("\nUnittest results = {} match rate or {} matches out of {} cases"
					.format(correct/total_tests_num,correct, total_tests_num))

	if(verbose):
		print("\nDEBUGGING INFO:")
		print("The Hashing Algos being used in this unittest\n{}"
													.format(thashing_algos))
		print("Number of hash algos being tested = {}".format(num_algos))
		print("The Encoding Styles being used in this unittest\n{}"
													.format(tencoding_set))
		print("Number of encoding styles being tested = {}".format(num_enset))
		print("The Test Strings being used in this unittest\n{}"
													.format(tstring_set))
		print("Number of test strings being tested = {}".format(num_tstrings))
	return

if __name__ == '__main__':
	unit_test("privacy_utility_unittest_param.txt",
							"privacy_utility_tests.txt",verbose=1)
