from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions
from bs4 import BeautifulSoup
from enum import Enum
import time, re, random, datetime, json

#libraries defined in this repository
import email_utility as eu 
import privacy_utility as pu 

import cred #python file that contains venmo login information
#This is excluded from the github commit for obvious reasons


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
	file.write('{} = {}\n'.format(usr,enc_un))
	file.close()
	return;

def add_transaction(fname,pyr,pye,des,year,month,day,ps):
	file = open(fname,'a')
	file.write('pyr: {}, pye: {}, desc: {}, year: {}, month: {}, day: {}, prset: {}\n'.format(pyr,pye,des,year,month,day,ps))
	file.close()
	return;

#function that helps deal with the weird date-keeping on the site
#TODO, make sure this works 100%, I am only 99.99% sure it works all the time
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
			year = cyear - 1
		else:
			year = cyear 

	return year,month,day

#TODO, make sure that the crawler then navigates to the state it should be in
def gen_crawl(jsfname,prof_un,pause_timer=30,var=5,verbose=True,**html_resources):
	a = alpha_crawler(prof_un,pause_timer=pause_timer,var=var,verbose=verbose,**html_resources)
	jsf = open(jsfname, 'r')
	data = json.loads(jsf.read())
	
	a.pstate = Dstate(data['pstate'])
	a.cstate = Dstate(data['cstate'])
	a.profile = data['profile']
	a.prev_profile = data['prev_profile']
	a.current_profile = data['current_profile']

	a.visited = data['visited']
	a.to_visit = data['to_visit']
	a.no_visit = data['no_visit']

	a.cprint('loaded the crawler data - now confirming')
	a.print_state()
	return a;


class alpha_crawler():
#----------------------------------------------------------------------------
	def __init__(self,prof_un,pause_timer=30,var=5,verbose=True,**html_resources):
		self.pstate = None
		self.cstate = None
		self.profile = '/' + prof_un
		self.prev_profile = None
		self.current_profile = None

		self.visited = dict()
		self.to_visit = list()
		self.no_visit = dict()

		self.ptimer = pause_timer 
		self.var = var
		self.verbose = verbose
		self.resc = html_resources
		browser_options = webdriver.ChromeOptions()
		browser_options.add_argument('--incognito')
		self.driver = webdriver.Chrome(options=browser_options)
		self.cprint('Created Crawler')
		return;

	def open_website(self,x=0,y=0,width=1000,length=800):
		self.cprint('\tOpening Website')
		self.driver.get(self.resc['login-url'])
		self.driver.set_window_size(width,length)
		self.driver.set_window_position(x,y)
		self.change_state(Dstate.LOGIN)
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

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

	def click_send_authentication_code(self):
		send_auth_code_button=self.driver.find_element_by_class_name(self.resc['button_class_name'])
		send_auth_code_button.click()
		self.cprint('\tClicked the (Send Authentication Code) button')
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	def get_authentication_code(self,email_un,email_pw,imap_url):
		#Keep in mind that the structure of a venmo auth code is 
		#"Your Venmo verification code is XXXXXX" (6 numbers)
		#With Email forwarding it is: 
		#"Received SMS: Your Venmo verification code is 00000, Sender: 86753"
		#If any of that changes, we're going to have to change the program that extracts 
		#the auth number 

		#This will also BREAK/Not work if the email does not come from uchicagoamp@gmail.com
		interface = eu.email_interface(email_un,email_pw,imap_url)
		auth_emails = interface.find_emails_from(email_un)
		auth_text = interface.extract_last_email(auth_emails)
		print(auth_text)
		match = re.findall(r'\tverification code is \d\d\d\d\d\d',auth_text)
		if(not match):
			self.cprint('Seems to be an error with getting the auth code')
			exit()
		else:
			ac = (match[0])[-6:]
			self.cprint('Got the authentication code: {}'.format(ac))
			self.pause_crawler(self.ptimer, variation=self.var)
			return ac

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

	def click_href(self, relative_url):
		#this emultes a user clicking on a link rather than typing in a url
		link = self.driver.find_element_by_xpath('//a[@href="{}"]'.format(relative_url))
		self.cprint('Clicking the {} url'.format(relative_url))
		link.click()
		return;

	def change_state(self, nstate):
		self.pstate = self.cstate
		self.cstate = nstate
		self.cprint('Previous state = {}'.format(self.pstate))
		self.cprint('Changing state to: {}'.format(nstate))
		return;

	def change_profile(self, nprof):
		self.prev_profile = self.current_profile
		self.current_profile = nprof
		self.cprint('Previous profile is now old profile: {}'.format(self.prev_profile))
		self.cprint('Changing profile to: {}'.format(nprof))
		return;

	def cprint(self, p): #CPrint = Crawler Print 
		if(self.verbose):
			print(p)
			return;
		return;

	def print_state(self):
		print('------printing state of crawler------')
		print('crawler account: {}'.format(self.profile))
		print('current state: {}'.format(self.cstate))
		print('current visited prof {}'.format(self.current_profile))
		print('------printing past state------------')
		print('previous state: {}'.format(self.pstate))
		print('previous visited prof {}'.format(self.prev_profile))
		print('------printing data struct-----------')
		print('VISITED = {}'.format(self.visited))
		print('TO VISIT = {}'.format(self.to_visit))
		print('NO VISIT = {}'.format(self.no_visit))
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
		self.cprint('\t\tSleeping for {} secs'.format(rounds(st,3)))
		time.sleep(st)
		self.cprint('\t\tDone Sleeping')
		return;

	def pause_crawler_mm(self,mini,maxi):
		st = random.uniform(mini,maxi)
		self.cprint('\t\tSleeping for {} secs'.format(rounds(st,3)))
		time.sleep(st)
		self.cprint('\t\tDone Sleeping')
		return; 

	#make this less useless
	def exit_browser(self,error_msg):
		print('Shutting down browser: {}'.format(error_msg))
		self.driver.quit()

	def save_state(self,fname):
		state = dict()
		state['pstate'] = self.pstate.value
		state['cstate'] = self.cstate.value
		state['profile'] = self.profile
		state['prev_profile'] = self.prev_profile
		state['current_profile'] = self.current_profile

		state['visited'] = self.visited
		state['to_visit'] = self.to_visit
		state['no_visit'] = self.no_visit

		f = open(fname, 'w')
		f.write(json.dumps(state))
		f.close()
		return;

#----------------------------------------------------------------------------
	def navigate(self,cmd,relative_url):
		switch = {
			'logout':(self.click_href, Dstate.LOGGEDOUT, None), 
			'home':(self.click_href, Dstate.HOME, None),
			'flist':(self.click_href, Dstate.FLIST, None),
			'pprof':(self.click_href, Dstate.PERSONAL, self.profile), 
			'coprof':(self.click_href, Dstate.PROFILE, relative_url),
			'fwd': (self.driver.forward, self.pstate, self.prev_profile),
			'back': (self.driver.back, self.pstate, self.prev_profile)
		}

		stidx = switch.get(cmd, lambda: self.cprint('invalid command given\n'))
		exefunc = stidx[0]
		self.cprint('\tBeginning Navigation: {}'.format(cmd))
	
		self.change_state(stidx[1])
		self.change_profile(stidx[2])
		#I don't like this approach but I think this is the only "compactish" way to do it for now		
		if(cmd == 'fwd' or cmd == 'back'): 
			exefunc()
		else:
			exefunc(relative_url)
			
		self.cprint('\tDone Navigating')
		self.pause_crawler(self.ptimer, variation=self.var)
		return;

	def navf(self,un):
		self.navigate('coprof',un)
		if(self.visited.get(un) != None):
			self.visited[un] = self.visited[un] + 1
			print('\tvisited: {} AGAIN! Upping count'.format(un))
		else: #when se
			self.visited[un] = 0
			print('\tvisited: {}! Adding to the visited list'.format(un))

	#This works, but it doesn't even matter, the users are all pre-loaded onto the page
	def click_view_all(self):
		if(self.cstate != Dstate.PROFILE):
			raise ValueError('profile does not fit the choices: {}'.format(valid_args))

		button = self.driver.find_element_by_partial_link_text('View All')
		button.click()
		self.cprint('\tclicking the (View All) button')
		return;

	def ex_users(self,fname):
		if(not (self.cstate == Dstate.FLIST or self.cstate == Dstate.PROFILE)):
			raise ValueError('Incorrect state: {}'.format(self.cstate))

		usernames = []
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
					usernames.append(match[0])
					add_user(fname,match[0])

		else: 
			self.cprint('Extracting other profile usn')
			fs = self.driver.find_elements_by_class_name(self.resc['friend_image'])
			for nested_element in fs:
				
				user = nested_element.get_attribute(self.resc['friend_image_details'])
				match = re.findall(r'\([\w|\W]+\)',user)
				if(match):
					a = a + 1
					#indexing like this will remove the parenthesises
					temp = '/' + match[0][1:-1]
					usernames.append(temp)
					add_user(fname,temp)

			
		self.cprint('\tusers here = {}'.format(usernames))
		self.cprint('\tlength of list = {}'.format(a))
		self.cprint('Done extracting')
		self.to_visit.extend(usernames)
		# self.cprint('printing new to_visit: {}'.format(self.to_visit))
		return;

	def expand_transaction_list(self):
		if(not (self.cstate == Dstate.PROFILE or self.cstate == Dstate.PERSONAL)):
			raise ValueError('Incorrect state: {}'.format(self.cstate))

		#More button: Class = moreButton "More"
		#More button: Class = moreButton "No more payments"
		expand_list = True
		while(expand_list):
			try:
				more_button = self.driver.find_element_by_link_text(self.resc['more_href'])
				more_button.click()
				self.cprint('\tPressed the (More) button')
			except selenium.common.exceptions.NoSuchElementException:
				# self.cprint('There is no more (More) buttons to press')
				expand_list = False

			self.pause_crawler(self.ptimer,variation=self.var)

		self.cprint('\tDone expanding list on prof')
		return;

	def ex_trans(self, fname):
		if(not (self.cstate == Dstate.PERSONAL or self.cstate == Dstate.PROFILE)):
			raise ValueError('Incorrect state: {}'.format(self.cstate))

		self.expand_transaction_list()
	 
		self.cprint('\tExtracting...')
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

			add_transaction(fname,payer,payee,description,year,month,day,privacy)

		self.cprint('\tLength of extracted list = {}'.format(a))
		self.cprint('\tDone extracting')
		return;

#----------------------------------------------------------------------------
	def run(self,v_un,v_pw,email_un,email_pw,ftrnx,fusr,fsave,imap_url='imap.gmail.com'):
		try: 
			self.open_website()
			self.login(v_un,v_pw)
			self.click_send_authentication_code()
			self.pause_crawler(10, variation = 2)
			# auth_code=self.get_authentication_code(email_un,email_pw,imap_url)
			# self.pause_crawler(10, variation = 2)
			# self.enter_authentication_code(auth_code)
			
			self.pause_crawler(30,variation=5)
			self.change_state(Dstate.HOME)
			self.change_profile('')

			self.navigate('pprof', self.profile)
			self.navigate('flist','/friends')
			self.pause_crawler(30,variation=10)
			self.ex_users(fusr)

			self.pause_crawler(20,variation=4)
			while(self.to_visit):

				dequ = self.to_visit.pop(0)
				try:
					self.navf(dequ)
					self.ex_users(fusr) #TODO
				except:
					self.to_visit.append(dequ)

				self.pause_crawler(5,variation=2)
				self.navigate("back",None)
				self.pause_crawler(4,variation=2)
		except Exception as e:
			print(e)
			print("ran into exception, saving state")
			# self.save_state(fsave)

		# print(self.visited)
		# print(len(self.visited))
		# print(self.to_visit)
		# print(len(self.to_visit))

#----------------------------------------------------------------------
		# self.navigate('pprof', self.profile) #go to crawler's profile
		# self.ex_trans(ftrnx)
		# # self.ex_usr(fusr)
		# self.pause_crawler(20, variation = 6)
		# self.navigate('back', None) #go back to home
		# self.pause_crawler(20, variation = 6)
		# self.navigate('fwd', None) # go back forward to personal profile
		# self.pause_crawler(20, variation = 6)

		# self.navigate('flist','/friends')
		# self.pause_crawler(20, variation = 6)

		# self.navigate('coprof','/Ranjan-Guniganti')
		# self.pause_crawler(20, variation = 6)
		# self.ex_trans(ftrnx)
		# # self.ex_usr(fusr)
		# self.pause_crawler(20, variation = 6)
		# self.navigate('back', None) #go back to home
		# self.pause_crawler(20, variation = 6)

		# self.navigate('coprof','/yyedward')
		# self.pause_crawler(20, variation = 6)
		# self.ex_trans(ftrnx)
		# # self.ex_usr(fusr)
		# self.pause_crawler(20, variation = 6)
		# self.navigate('back', None) #go back to home
		# self.pause_crawler(20, variation = 6)

		# self.navigate('pprof', self.profile) #go bacl to home
		# self.pause_crawler(20, variation = 6)
		# self.navigate('home', "/")		
		# self.pause_crawler(20, variation = 6)
		# self.navigate('back', None) #go back to pprof
		# self.pause_crawler(20, variation = 6)
		# self.navigate('flist', "/friends")
		# self.pause_crawler(20, variation = 6)
		# self.navigate('logout',"/account/logout")
#----------------------------------------------------------------------

#----------------------------------------------------------------------
		# self.navigate('pprof', self.profile)
		# self.pause_crawler(20,variation =6)
		# self.ex_trans(ftrnx)
		# self.navigate('flist','/friends')
		# self.pause_crawler(20,variation = 3)
		# self.ex_users(fusr)
		# # self.navigate('coprof',"/Ted-Kim-14")
		# self.navigate('coprof',"/Ranjan-Guniganti")
		# self.pause_crawler(20,variation = 3)
		# self.ex_users(fusr)
		# self.ex_trans(ftrnx)
#----------------------------------------------------------------------

		# except: 
			# eu.send_email('smtp.gmail.com',email_un,"tedkim97@uchicago.edu",
										# email_pw,"error","hihi test message 2")


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
		'privacy_set':'id2'
	}
	a = alpha_crawler(cred.v_prof,pause_timer=5,var=1,verbose=True,**html_info)
	# a = gen_crawl("one.save",cred.v_prof,pause_timer=5,var=1,verbose=True,**html_info)
	a.run(cred.v_username2,cred.v_password2,cred.v_email_un,cred.v_email_pd,'data/one.trnx','data/one.usr','data/one.save')
	