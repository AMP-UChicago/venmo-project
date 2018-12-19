#Library used to protect privacy 
import hashlib

# Be careful about what you enter into these functions, cryptographic functions are 
# one-way, meaning we cannot revert/figure out the original input through the output

def convert_to_hash(username: str, encoding: str):
	# This seems super redundant and not pythonic, so I might just delete this later
	m = hashlib.sha256(username.encode(encoding))
	return m.hexdigest()

if __name__ == '__main__':
	# print(convert_to_hash('abc'))
	# print(convert_to_hash('abc'))
	# print(convert_to_hash('def'))
	# print(convert_to_hash('qqq'))
	# print(convert_to_hash('ttt'))
	# print(convert_to_hash('zzz'))
	print(hashlib.algorithms_available)
	print(hashlib.algorithms_guaranteed)
	print("🤦‍♀️🙌🤦‍♀️🤦‍♀️🤦‍♀️🤦‍♀️🤦‍♀️🤦‍♀️🤦‍♀️🤦‍♀️🤦‍♀️🤦‍♀️🤦‍♀️")