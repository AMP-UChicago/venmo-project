import re

def reduce_usr(fname):
	unproc = set()
	f = open(fname, "r")
	for cnt, line in enumerate(f):
		unproc.add(line.strip())

	f.close()

	g = open(fname,"w")
	count = 0
	popped = 1
	try: 
		while(popped):
			popped = unproc.pop()
			g.write("{}\n".format(popped))
			count+=1
	except KeyError: 
		g.close()
		print("length of the set".format(count))

def validate_usr(original,new):
	f1 = open(original, "r")
	s1 = set()
	for cnt1, line1 in enumerate(f1):
		s1.add(line1.strip())

	f2 = open(new, "r")
	s2 = set()
	for cnt2,line2 in enumerate(f2):
		s2.add(line2.strip())

	print("length of set in f1 = {}".format(len(s1)))
	print("length of set in f2 = {}".format(len(s2)))
	a = (s2 ^ s1)
	print("differences in original and new= {}".format(a))
	if(a == set()):
		print("It seems that the new file has the same set!")


if __name__ == "__main__":
	# reduce_usr("three.usr")
	# validate_file("three1.usr","three.usr")
	print("done")