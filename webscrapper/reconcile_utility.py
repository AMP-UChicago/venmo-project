import re

def reduce_usr(fname,suffix,name_delta):
	unproc = set()
	f = open(fname, "r")
	for cnt, line in enumerate(f):
		unproc.add(line.strip())
	f.close()

	split_ind = (len(suffix) + 2)*-1
	mod_fname = fname[:split_ind] + name_delta + fname[split_ind:]
	# mod_fname = fname+name_delta+suffix

	g = open(mod_fname,"w")
	count = 0
	popped = 1
	try: 
		while(popped):
			popped = unproc.pop()
			g.write("{}\n".format(popped))
			count+=1
	except KeyError: 
		g.close()
		print("wrote reduced form to new file: {}".format(mod_fname))
		print("length of the set {}".format(count))

	return;

def validate_usr(orig,new):
	print("hihi")
	f1 = open(orig, "r")
	s1 = set()
	for cnt1, line1 in enumerate(f1):
		s1.add(line1.strip())
	f1.close()

	f2 = open(new, "r")
	s2 = set()
	for cnt2,line2 in enumerate(f2):
		s2.add(line2.strip())
	f2.close()

	print("length of set in f1 = {}".format(len(s1)))
	print("length of set in f2 = {}".format(len(s2)))
	a = (s2 ^ s1)
	print("differences in original and new= {}".format(len(a)))
	if(a == set()):
		print("It seems that the new file has the same set!")
	return;

def reduce_trnx(fname,suffix,name_delta):
	return;

def validate_usr(orig,new):
	return;


if __name__ == "__main__":
	reduce_usr("/media/sf_E_DRIVE/data/test3.usrs","usr","_reduced")
	# validate_usr('a','b')
	validate_usr("/media/sf_E_DRIVE/data/test3.usrs","/media/sf_E_DRIVE/data/test3_reduced.usrs")