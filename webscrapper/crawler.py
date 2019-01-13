from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions
from bs4 import BeautifulSoup
from enum import Enum
import time, re, random, datetime, json, threading

#libraries defined in this repository
import email_utility as eu 
import privacy_utility as pu 

import cred #python file that contains venmo login information
#This is excluded from the github commit for obvious reasons


#TODO - maybe remove the SET() implementation of the "TO VISIT"

class Dstate(Enum):
	LOGIN = 1 
	HOME = 2
	PERSONAL = 3
	FLIST = 4
	PROFILE = 5
	LOGGEDOUT = 6

def add_user(fname,usr):
	file = open(fname,'a')
	enc_un = pu.hash_username(usr)
	file.write('{} -> {}\n'.format(usr,enc_un))
	file.close()
	return;

def add_transaction(fname,pyr,pye,des,year,month,day,ps):
	file = open(fname,'a')
	pyr_enc = pu.hash_username(pyr)
	pye_enc = pu.hash_username(pye)
	file.write('pyr: {}, pye: {}, desc: {}, year: {}, month: {}, day: {}, prset: {}\n'.format(pyr_enc,pye_enc,des,year,month,day,ps))
	file.close()
	return;

#function that helps deal with the weird date-keeping on the site
def conv_date(date:str):
	today = datetime.datetime.now()
	cday = today.day
	cmonth = today.month
	cyear = today.year

	mk = {
		'january':1,
		'february':2,
		'march':3,
		'april':4,
		'may':5,
		'june':6,
		'july':7,
		'august':8,
		'september':9,
		'october':10,
		'november':11,
		'december':12
	}
	proc_str = date.lower()

	edgec = re.findall(r'ago',date)
	if(edgec):
		return cyear,cmonth,cday

	month = mk.get((re.findall(r'[a-z]+',proc_str))[0],0)

	regyr = re.findall(r'\d\d\d\d',proc_str)
	if(regyr):
		day = int((re.findall(r'\d{1,2}',proc_str))[0])
		year = int(regyr[0])
		
	else:
		day = int((re.findall(r'\d{1,2}',proc_str))[0])
		mcur = 100*cmonth + cday 
		mtrx = 100*month + day
		if(mtrx > mcur):
			if(cyear == 1):
				year = 12
			else:
				year = cyear - 1
		else:
			year = cyear

	return year,month,day

class alpha_crawler():
	def __init__(self,pause_timer=20,var=2,verbose=True):
		self.crwid = None
		self.base_url = None
		self.ptimer = pause_timer
		self.var = var
		self.resc = None
		self.verbose = verbose

		self.personal = None
		self.curr_prof = None
		self.prev_prof = None
		self.cstate = None
		self.pstate = None

		self.visited = None
		self.visited_len = 0
		self.to_visit = None
		self.to_visit_len = 0
		self.to_visit_q = None
		self.to_visit_q_len = 0
		self.no_visit = None

		self.locked = False

		browser_options = webdriver.ChromeOptions()
		browser_options.add_argument('--incognito')
		self.driver = webdriver.Chrome(options=browser_options)
		self.cprint('Created Crawler')
		return;

	def load_properties_man(self,crwid,prof,burl,html_resc,pause_timer,var,verbose):
		self.crwid = crwid
		self.base_url = burl
		self.ptimer = pause_timer
		self.var = var
		self.resc = html_resc
		self.verbose = verbose

		self.personal = prof
		self.curr_prof = None
		self.prev_prof = None
		self.cstate = None
		self.pstate = None

		self.visited = dict()
		self.visited_len = 0
		self.to_visit = set()
		self.to_visit_len = 0
		self.no_visit = dict()

		self.locked = False
		return;
	#initializing an instance from a file
	def load_properties(self,fname):
		f = open(fname, "r")
		params = json.loads(f.read())
		self.crwid = params['crwid']
		self.base_url = params['base_url']
		self.ptimer = params['ptimer']
		self.var = params['var']
		self.resc = params['resc']
		self.verbose = params['verbose']

		self.personal = params['personal']
		self.curr_prof = params['curr_prof']
		self.prev_prof = params['prev_prof']
		self.cstate = params['cstate']
		self.pstate = params['pstate']

		self.visited = params['visited']
		self.visited_len = params['visited_len']
		self.to_visit = set(params['to_visit'])
		self.to_visit_len = params['to_visit_len']
		self.no_visit = params['no_visit']

		self.locked = params['locked']
		f.close()
		
		self.cprint("Done Initializing")
		# self.print_state()
		# print(params)
		return;

#------------------------------------------------------------------------------
	#final
	def open_website(self,xpos=0,ypos=0,width=800,length=800):
		self.cprint('\tOpening Website')
		self.driver.get(self.resc['login-url'])
		self.driver.set_window_size(width,length)
		self.driver.set_window_position(xpos,ypos)
		self.change_state(Dstate.LOGIN)
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	#final
	def login(self,username,password):
		uname_ele = self.resc['username_html_element']
		pword_ele = self.resc['password_html_element']
		button_ele = self.resc['button_class_name']

		uname_html = self.driver.find_element_by_name(uname_ele)
		pword_html = self.driver.find_element_by_name(pword_ele)

		uname_html.send_keys(username)
		pword_html.send_keys(password)
		self.pause_crawler(self.ptimer,variation=self.var) 


		self.cprint('\tTyped in credentials')
		login_button = self.driver.find_element_by_class_name(button_ele)
		login_button.click()
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	#final
	def click_send_authentication_code(self):
		send_auth_code_button=self.driver.find_element_by_class_name(self.resc['button_class_name'])
		send_auth_code_button.click()
		self.cprint('\tClicked the (Send Authentication Code) button')
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	#final
	def get_authentication_code(self,email_un,email_pw,imap_url):
		#Keep in mind that the structure of a venmo auth code is 
		#"Your Venmo verification code is XXXXXX" (6 numbers)
		#With Email forwarding it is: 
		#"Received SMS: Your Venmo verification code is 00000, Sender: 86753"
		#If any of that changes, we're going to have to change the program that extracts 
		#the auth number 

		#This will also BREAK/Not work if the email does not come from uchicagoamp@gmail.com
		interface = eu.email_interface(email_un,email_pw,imap_url)
		auth_emails = interface.find_emails_from(email_un) #find emails from the email 
		#associated with this account 
		auth_text = interface.extract_last_email(auth_emails)
		print(auth_text)
		match = re.findall(r'verification code is \d\d\d\d\d\d',auth_text)
		if(not match):
			self.cprint('Seems to be an error with getting the auth code')
			exit()
		else:
			ac = (match[0])[-6:]
			self.cprint('Got the authentication code: {}'.format(ac))
			self.pause_crawler(self.ptimer, variation=self.var)
			return ac

	#final
	def enter_authentication_code(self, code:str):
		auth_code = self.driver.find_element_by_name(self.resc['auth_html_element'])
		auth_code.send_keys(code)
		self.cprint('\tEntered the authentication code')
		submit_code_button = self.driver.find_element_by_class_name(self.resc['button_class_name'])
		submit_code_button.click()
		self.cprint('\tClicked (Submit)')
		self.pause_crawler(self.ptimer,variation=self.var)

		buttons = self.driver.find_elements_by_class_name(self.resc['button_class_name'])
		buttons[1].click()
		self.cprint('\tClicked (Not Now)')
		self.change_state(Dstate.HOME)
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	#final
	def change_state(self, nstate):
		self.pstate = self.cstate
		self.cstate = nstate
		self.cprint('Previous state = {}'.format(self.pstate))
		self.cprint('Changing state to: {}'.format(nstate))
		return;

	#final
	def change_profile(self, nprof):
		self.prev_prof = self.curr_prof
		self.curr_prof = nprof
		self.cprint('Previous profile is now old profile: {}'.format(self.prev_prof))
		self.cprint('Changing profile to: {}'.format(nprof))
		return;

	def cprint(self, p): #CPrint = Crawler Print 
		if(self.verbose):
			print(p)
			return;
		return;

	def print_state(self):
		print('------printing state of crawler------')
		print('crawler personal: {}'.format(self.personal))
		print('crawler id: {}'.format(self.crwid))
		print('current state: {}'.format(self.cstate))
		print('current visited prof {}'.format(self.curr_prof))
		print('------printing past state------------')
		print('previous state: {}'.format(self.pstate))
		print('previous visited prof {}'.format(self.prev_prof))
		print('------printing data struct-----------')
		print('NUM VISITED = {}'.format(self.visited_len))
		print('NUM TO VISIT = {}'.format(self.to_visit_len))
		print('---------Done Printing State---------')
		return;

	def pause_crawler(self,sec,variation=0):
		st = random.uniform(sec-variation,sec+variation)
		self.cprint('\t\tSleeping for {} secs'.format(round(st,3)))
		time.sleep(st)
		self.cprint('\t\tDone sleeping')
		return; 

	def pause_crawler_v2(self):
		st = random.uniform(self.ptimer - self.var, self.ptimer + self.var)
		self.cprint('\t\tSleeping for {} secs'.format(round(st,3)))
		time.sleep(st)
		self.cprint('\t\tDone Sleeping')
		return;

	def pause_crawler_mm(self,mini,maxi):
		st = random.uniform(mini,maxi)
		self.cprint('\t\tSleeping for {} secs'.format(round(st,3)))
		time.sleep(st)
		self.cprint('\t\tDone Sleeping')
		return; 

	#make this less useless
	def exit_browser(self,error_msg):
		print('Shutting down browser: {}'.format(error_msg))
		self.driver.quit()
#------------------------------------------------------------------------------

	def save_state(self,fname):
		state = dict()
		#ENUMS can't be json serialized
		state['crwid'] = self.crwid
		state['base_url'] = self.base_url
		state['ptimer'] = self.ptimer
		state['var'] = self.var
		state['resc'] = self.resc

		state['personal'] = self.personal
		#Edge case with enumerations
		if(self.pstate == None):
			state['pstate'] = 0
		else:
			state['pstate'] = self.pstate.value 

		if(self.pstate == None):
			state['cstate'] = 0
		else:
			state['cstate'] = self.cstate.value
		
		state['prev_prof'] = self.prev_prof
		state['curr_prof'] = self.curr_prof

		state['visited'] = self.visited
		state['visited_len'] = self.visited_len
		#Sets can also not be JSON serialized
		state['to_visit'] = list(self.to_visit)
		state['to_visit_len'] = self.to_visit_len
		state['no_visit'] = self.no_visit

		state['locked'] = self.locked

		f = open(fname, 'w')
		f.write(json.dumps(state))
		f.close()
		return;

	#----------------Navigation/Interaction Func--------------------------------
	def click_href(self, relative_url):
		#this emulates a user clicking on a link rather than typing in a url
		link = self.driver.find_element_by_xpath('//a[@href="{}"]'.format(relative_url))
		self.cprint('Clicking the {} url'.format(relative_url))
		link.click()
		return;

	#Even though this can skip to any url, it shall ONLY be used to skip to a prof
	#which is why it is set up in this context 
	def skip_to_url(self, un):
		self.change_state(Dstate.PROFILE)
		self.change_profile(un)
		self.driver.get(self.base_url + un)
		self.cprint('Skipping directly to {}'.format(un))
		return;

	def click_img(self, un):
		if(self.cstate != Dstate.PROFILE):
			raise ValueError('Not the right state in (Dstate.PROFILE)')

		self.click_view_all()
		snip = un[1:]
		plink = self.driver.find_element_by_xpath('//*[contains(@details,"{}")]'.format(snip))
		self.cprint('clicking the image link {}'.format(un))
		plink.click()
		return;

	def click_view_all(self):
		if(self.cstate != Dstate.PROFILE):
			raise ValueError('profile does not fit the choices: {}'.format(valid_args))

		buttons = self.driver.find_elements_by_partial_link_text('View All')
		for x in buttons:
			x.click()
		self.cprint('\tclicked all the (View All) button')
		return;

	def expand_transaction_list(self):
		if(not (self.cstate == Dstate.PROFILE or self.cstate == Dstate.PERSONAL)):
			raise ValueError('Incorrect state: {}'.format(self.cstate))

		count = 0 

		expand_list = True
		while(expand_list):
			try:
				more_button = self.driver.find_element_by_link_text(self.resc['more_href'])
				# print(self.resc['more_href'])
				more_button.click()
				count += 1
				# blah = self.driver.find_element_by_link_text(self.resc['more_bug'])
				self.cprint('\tPressed the (More) button')
			except selenium.common.exceptions.NoSuchElementException:
				# self.cprint('There is no more (More) buttons to press')
				expand_list = False

			self.pause_crawler(5,variation=1)
			#Countermeasure in place to overcome a very specific edge case
			if(count >= 20):
				return
		self.cprint('\tDone expanding list on prof')
		return;

	#----------------------Interrupt Checking Functions-------------------------
	def check_limited(self):
		while(True):
			try:
				self.driver.find_element_by_xpath('//*[contains(text(),"{}")]'.format(self.resc['lim']))
				self.locked = True
				self.cprint("hit a rate limit, killing process")
				raise ValueError("hit a rate limit") #TODO, CHANGE THIS LATER
			except selenium.common.exceptions.NoSuchElementException:
				return;
		return;
	
	def check_disconnect(self):
		while(True):
			try:
				self.driver.find_element_by_xpath('//*[contains(text(),"{}"]'.format(self.resc['502']))
				self.cprint("hit a bad gateway, refreshing")
				self.driver.refresh()
			except:
				return;
		return;

	def check_invalid(self):
		while(True):
			try: 
				self.driver.find_element_by_xpath('//*[contains(text(),"{}")]'.format(self.resc['bad_url']))
				self.cprint("invalid url, going back")
				self.navigate('back',None)
			except: 
				return;
		return;

	def navigate(self,cmd,relative_url):
		switch = {
			'logout':(Dstate.LOGGEDOUT, None, self.click_href), 
			'home':(Dstate.HOME, None, self.click_href),
			'flist':(Dstate.FLIST, None, self.click_href),
			'pprof':(Dstate.PERSONAL, self.personal, self.click_href), 
			'coprof':(Dstate.PROFILE, relative_url, self.click_href, self.click_img),
			'fwd': (self.pstate, self.prev_prof, self.driver.forward),
			'back': (self.pstate, self.prev_prof, self.driver.back)
		}

		if(cmd == "coprof" and self.cstate == Dstate.PERSONAL):
			self.cprint("Can't access other profiles in PERSONAL state (Force Switching)")
			self.click_href('/friends')
			self.pause_crawler_mm(4,7)
			self.click_href(relative_url)
			self.change_state(Dstate.PROFILE)
			self.change_profile(relative_url)
			return;

		if(relative_url == self.personal and self.cstate == Dstate.PROFILE):
			# self.click_href(self.personal)
			# self.change_state(Dstate.PERSONAL)
			# self.change_profile(self.personal)
			# self.cprint("Special Situation, navigating back to personal")
			#we should never be returning to the personal state
			self.cprint("should not be re-visiting profile: SKIPPING")
			return; 

		stidx = switch.get(cmd, lambda: self.cprint('invalid command given\n'))
		exefunc = stidx[2]
		#not happy with this IF statement
		if((self.cstate == Dstate.FLIST) and (cmd == 'coprof')):
			exefunc = stidx[2]

		if((self.cstate == Dstate.PROFILE) and (cmd == 'coprof')):
			exefunc = stidx[3]

		self.cprint('\tBeginning Navigation: {}'.format(cmd))
	
		self.change_state(stidx[0])
		self.change_profile(stidx[1])

		if(cmd == 'fwd' or cmd == 'back'): 
			exefunc()
		else:
			exefunc(relative_url)
			
		self.cprint('\tDone Navigating')
		self.pause_crawler(self.ptimer, variation=self.var)
		return;

	def navpet(self,un,fusrs,ftrnx):
		if(self.no_visit.get(un,None) != None):
			self.cprint("hit someone on the no_visit list: {} SKIPPING".format(un))
			return;

		try:
			self.navigate('coprof',un)
		except selenium.common.exceptions.NoSuchElementException:
			self.skip_to_url(un)

		now = datetime.datetime.now()
		year,month,day = now.year, now.month, now.day  

		if(self.visited.get(un) != None):
			# self.visited[un] = self.visited[un] + 1
			self.cprint('\tvisited: {} AGAIN Updating last visit'.format(un))
		else:
			self.visited_len += 1
			self.cprint('\tvisited: {}! Adding to the visited list'.format(un))
			self.cprint('EXTRACTING!')
			self.ex_usrs(fusrs)
			self.ex_trnx(ftrnx)
			self.cprint('Done EXTRACTING!')

		self.visited[un] = (year,month,day)
		return;

	def ex_usrs(self,fusrs):
		if(not (self.cstate == Dstate.FLIST or self.cstate == Dstate.PROFILE)):
			raise ValueError('Incorrect state: {}'.format(self.cstate))

		usernames = set()
		a = 0
		#the two approaches to extracting friends are very different
		if(self.cstate == Dstate.FLIST):
			self.cprint('Extracting personal profile usn')
			table = self.driver.find_element_by_class_name(self.resc['personal_friendslist'])
			ihtml = table.get_attribute('innerHTML')
			page_content = BeautifulSoup(ihtml,'html.parser')
			parsed_elements = page_content.find_all('a')

			for element in parsed_elements:
				match = re.findall(r'[/][\w|\W]+',element.get('href'))
				if(match): #match is an empty list if there are no matches
					a = a + 1
					usr = match[0]
					#if the given user is not in the "NO VISIT" and "VISITED" pile....
					add_cond = ((self.no_visit.get(usr,None) == None) and (self.visited.get(usr,None) == None))
					if(add_cond):
						usernames.add(usr)
						add_user(fusrs,match[0])

		else: 
			self.cprint('Extracting other profile usn')

			fs = self.driver.find_elements_by_class_name(self.resc['friend_image'])
			for nested_element in fs:
				user = nested_element.get_attribute(self.resc['friend_image_details'])
				match = re.findall(r'\([\w|\W]+\)',user)
				if(match):
					#indexing like this will remove the parenthesises
					temp = '/' + match[0][1:-1]
					add_cond = ((self.no_visit.get(temp,None) == None) and (self.visited.get(temp,None) == None))
					if(add_cond):
						usernames.add(temp)
						add_user(fusrs,temp)

			a = len(usernames)

		if(a == 0):
			raise ValueError("Number of extracted friends should not be 0, possible error")

		self.cprint('\tlength of list = {}'.format(a))
		print(usernames)
		self.to_visit = (self.to_visit|usernames)
		self.to_visit_len += a 
		self.cprint('adding users to the TO_VISIT pile')
		return;

	def ex_trnx(self, ftrnx):
		if(not (self.cstate == Dstate.PERSONAL or self.cstate == Dstate.PROFILE)):
			raise ValueError('Incorrect state: {}'.format(self.cstate))

		self.expand_transaction_list()
	 
		self.cprint('\tExtracting TRNX...')
		raw_elements = self.driver.find_elements_by_class_name(self.resc['transaction_class'])

		trns = []
		a = 0 
		for x in raw_elements:
			box_content = BeautifulSoup(x.get_attribute('innerHTML'),'html.parser')
			
			#------Catches and situations where we would not extract--------
			if(self.cstate == Dstate.PERSONAL):
				privacy = (box_content.find(self.resc['privacy_tag'],self.resc['privacy_class'])).get(self.resc['privacy_set']).strip()

			unames = box_content.find_all('a')

			first = unames[0].get('href')
			second = unames[3].get('href')
			if(first == '/' or second == '/'):
				self.cprint('hit a transaction with a blocked user: skipping\n-------')
				continue

			#------Data collection and such--------
			a = a + 1 

			description = (box_content.find(self.resc['desc_tag'],style=self.resc['desc_style'])).getText().strip()
			date = (box_content.find(self.resc['date_tag'],self.resc['date_class'])).getText().strip()
			year, month, day = conv_date(date)
			privacy = 'unknown' #TODO, FIX THIS/IMPLEMENT THIs
			
			pd = box_content.find('div','m_five_t p_ten_r').getText() #pdt = pd.getText().replace(" ","")
			paydir = re.findall(r'charged',pd) # probably should make this an ifelse statement
			if(paydir):
				payer = second
				payee = first
				self.cprint('{} {} {} on (m,d,y)=({} , {}, {})\n text: {} \n privacy:{}\n--------'.format(payee,paydir[0],payer,month,day,year,description,privacy))
				
			paydir2 = re.findall(r'paid',pd)
			if(paydir2):
				payer = first
				payee = second
				self.cprint('{} {} {} on (m,d,y)=({} , {}, {})\n text: {} \n privacy:{}\n--------'.format(payer,paydir2[0],payee,month,day,year,description,privacy))

			add_transaction(ftrnx,payer,payee,description,year,month,day,privacy)

		# self.cprint('\tLength of extracted list = {}'.format(a))
		self.cprint('\tDone extracting')
		return;


	def set_up(self,fusr,ftrnx):
		self.navigate('pprof', self.personal)
		self.visited[self.personal] = (0,0,0)
		self.ex_trnx(ftrnx)
		self.pause_crawler(3,variation = 1)
		self.navigate('flist','/friends')
		self.pause_crawler(3,variation = 1)
		self.ex_usrs(fusr)
		self.pause_crawler(5,variation=1)

		t1 = threading.Thread(target=self.check_invalid())
		t2 = threading.Thread(target=self.check_disconnect())
		t3 = threading.Thread(target=self.check_limited())
		t1.start()
		t2.start()
		t3.start()
		if(self.curr_prof != None):
			self.skip_to_url(self.curr_prof)

	def pogo_search(self,fusr,ftrnx,limit = 80):
		# self.navigate('pprof', self.personal)
		# self.visited[self.personal] = (0,0,0)
		# self.ex_trnx(ftrnx)
		# self.pause_crawler(3,variation = 1)
		# self.navigate('flist','/friends')
		# self.pause_crawler(3,variation = 1)
		# self.ex_usrs(fusr)
		# self.pause_crawler(5,variation=1)

		while(self.to_visit):
			if(self.visited_len >= limit):
				break

			try: 
				rand = self.to_visit.pop()
				self.navpet(rand,fusr,ftrnx)
				# self.ex_trnx()
			except KeyError: 
				self.cprint("List is empty - Conclusion")
				self.exit_browser("No error - completely fine")
				exit()

			self.pause_crawler(5, variation = 1)
			print("length of visited = {}".format(self.visited_len))
			print("length of to visit = {}".format(self.to_visit_len))

			self.check_limited()
			self.check_disconnect()
			self.check_invalid()

		self.cprint("Reached the self defined limit")

	def test_file_run(self,param_file, cred_file, data_file):
		b = open(param_file, 'r')
		prms = json.loads(b.read())
		c = open(cred_file, 'r')
		creds = json.loads(c.read())
		d = open(data_file, 'r')
		dat = json.loads(d.read())

		try:
			self.open_website()
			self.login(creds['v_un'], creds['v_pw'])
			self.click_send_authentication_code()
			self.pause_crawler(180,variation =2)
			auth_code=self.get_authentication_code(creds['em_un'],creds['em_pw'],creds['imap'])
			self.pause_crawler(20, variation = 1)
			self.enter_authentication_code(auth_code)
			self.pause_crawler(8,variation=2)

			self.set_up(dat['usrs'],dat['trnx'])

			for x in range(25,40):
				self.pogo_search(dat['usrs'],dat['trnx'], limit = ((x+1) * 80))
				self.pause_crawler(1200,variation = 1)

		except KeyboardInterrupt: 
			self.save_state(dat['save'])
			print("CRAWLER EXIT THROUGH KEYBOARD INTERRUPT")
		except Exception as e:
			serv = creds['smtp']
			error_add = prms['error_email']
			subj = '[CRAWLER ERROR]'
			emsg = 'crawler has entered an exception: {}'.format(e) 
			print(e)
			print(emsg)
			eu.send_email(serv,creds['em_un'],error_add,creds['em_pw'],subj,emsg)
			self.save_state(dat['save'])
			print("saved the crawler")
		
		return;

	def file_run(self,param_file,cred_file,data_file):
		b = open(param_file, 'r')
		prms = json.loads(b.read())
		c = open(cred_file, 'r')
		creds = json.loads(c.read())
		d = open(data_file, 'r')
		dat = json.loads(d.read())

		try:
			self.open_website()
			self.login(creds['v_un'], creds['v_pw'])
			self.click_send_authentication_code()
			auth_code=self.get_authentication_code(creds['em_un'],creds['em_pw'],creds['imap'])
			self.pause_crawler(10, variation = 2)
			self.enter_authentication_code(auth_code)
			self.pause_crawler(10,variation=2)

			self.navigate('pprof', self.personal) #go to crawler's profile
			self.ex_trnx(dat['trnx'])
			self.navigate('flist','/friends')
			self.pause_crawler(10, variation = 6)
			self.ex_usrs(dat['usrs'])
			#Add Other stuff here 
			self.cprint("add other stuff here")

		except KeyboardInterrupt: 
			print("CRAWLER EXIT THROUGH KEYBOARD INTERRUPT")
		except Exception as e:
			serv = creds['smtp']
			error_add = prms['error_email']
			subj = '[CRAWLER ERROR]'
			emsg = 'crawler has entered an exception: {}'.format(e) 
			eu.send_email(serv,creds['em_un'],error_add,creds['em_pw'],subj,emsg)
			self.save_state(dat['save'])
			print("saved the crawler")
		
		return;

	def test_run(self,v_un,v_pw,email_un,email_pw,ftrnx,fusr,fsave,imap_url='imap.gmail.com'):
		# try:
		self.open_website()
		self.login(v_un,v_pw)
		self.click_send_authentication_code()
		self.pause_crawler(20, variation = 2)
		auth_code=self.get_authentication_code(email_un,email_pw,imap_url)
		self.pause_crawler(10, variation = 2)
		self.enter_authentication_code(auth_code)
		self.pause_crawler(10,variation=2)

		self.pogo_search(fusr)

	def run(self,v_un,v_pw,email_un,email_pw,ftrnx,fusr,fsave,imap_url='imap.gmail.com'):
		try:
			self.open_website()
			self.login(v_un,v_pw)
			self.click_send_authentication_code()
			self.pause_crawler(10, variation = 2)
			auth_code=self.get_authentication_code(email_un,email_pw,imap_url)
			self.pause_crawler(10, variation = 2)
			self.enter_authentication_code(auth_code)
			self.pause_crawler(20,variation=5)
			self.navigate('pprof', self.personal) #go to crawler's profile
			self.ex_trnx(ftrnx)
			self.navigate('flist','/friends')
			self.pause_crawler(10, variation = 6)
			self.ex_usrs(fusr)
			#Add Other stuff here 
			self.cprint("add other stuff here")

		except KeyboardInterrupt: 
			print("CRAWLER EXIT THROUGH KEYBOARD INTERRUPT")
		except Exception as e:
			serv = 'smtp.gmail.com'
			error_add = 'tedkim97@uchicago.edu'
			subj = '[CRAWLER ERROR]'
			emsg = 'crawler has entered an exception: {}'.format(e) 
			eu.send_email(serv,email_un,error_add,email_pw,subj,emsg)
			self.save_state(fsave)
			print("saved the crawler")


if __name__ == "__main__":
	html_info = {
		'login-url': 'https://venmo.com/account/sign-in',
		'username_html_element':'phoneEmailUsername',
		'password_html_element':'password',
		'button_class_name':'ladda-label',
		'auth_html_element':'token',
		'logout_href':'/account/logout',
		'flist_href':'/friends',
		'home_href':'/',
		'more_href':'More',
		'no_more_payments_href':'No more payments',
		'personal_friendslist':'settings-people-members',
		'friend_image':'anchor',
		'friend_image_details':'details',
		'transaction_class': 'profile_feed_story',
		'desc_tag':'div',
		'desc_style':'word-wrap:break-word',
		'date_tag':'a',
		'date_class':'gray_link',
		'privacy_tag':'span',
		'privacy_class':'audience_button',
		'privacy_set':'id2', 
		'lim':'maximum number of profile page views in an hour',
		'502':'502 Bad Gateway',
		'bad_url':'the page you requested does not exist'
	}
	# a = alpha_crawler(cred.v_prof,cred.burl,html_info,pause_timer=5,var=1,verbose=True)
	a = alpha_crawler()
	a.load_properties('crawler.params') #/media/sf_E_DRIVE/save3.params
	a.test_file_run('crawler.params','crawler.cred','crawler.data')
	# a = gen_crawl("one.save",cred.v_prof,pause_timer=5,var=1,verbose=True,**html_info)
	# a.test_run(cred.v_username2,cred.v_password2,cred.v_email_un,cred.v_email_pd,'data/one.trnx','data/one.usr','data/three.save')
	# a.run(cred.v_username2,cred.v_password2,cred.v_email_un,cred.v_email_pd,'data/one.trnx','data/one.usr','data/one.save')
