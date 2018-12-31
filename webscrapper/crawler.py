from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions
from enum import Enum
import time
import re
import random
from bs4 import BeautifulSoup

import cred #python file that contains venmo login information
#This is excluded from the github commit for obvious reasons

import email_utility as eu 
import privacy_utility as pu 


class Dstate(Enum):
	LOGIN = 1 
	HOME = 2
	PERSONAL = 3
	FLIST = 4
	PROFILE = 5
	LOGGEDOUT = 6

class activity():
	def __init__(self, send, rec, date, description, likes, ps):
		self.sender = send 
		self.receiver = rec 
		self.date = date 
		self.desc = description 
		self.nlikes = likes,
		self.ps = ps

	def prettyp(self):
		print("sender: {}, receiver {}, date {}, tagline {}, likes {}, privacy setting: {}\n---------------"
			.format(self.sender, self.receiver, self.date, self.desc, self.nlikes, self.ps))

def add_user(fname,usr):
	file = open(fname,"a")
	file.write("{}\n".format(usr))
	file.close()
	return;

def add_transaction(fname,trnx):
	file = open(fname, "a")
	file.write("\n")
	return;

def add_transaction_v2(fname,s,r,des,dat,ps):
	file = open(fname, "a")
	file.write("sender: {}, receiver: {}, text: {}, date: {} , privacy setting: {}\n".format(s,r,des,dat,ps))
	file.close()
	return;

class alpha_crawler():
	def __init__(self,prof_un,pause_timer=30,var=5,verbose=True,**html_resources):
		self.pstate = None
		self.cstate = None
		self.profile = "/" + prof_un
		self.current_profile = ""
		self.ptimer = pause_timer 
		self.var = var
		self.verbose = verbose
		self.resc = html_resources
		browser_options = webdriver.ChromeOptions()
		browser_options.add_argument("--incognito")
		self.driver = webdriver.Chrome(options=browser_options)
		return;

	def open_website(self,x=0,y=0,width=1000,length=800):
		self.cprint("Opening Website")
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
		self.cprint("Typed in username")
		self.pause_crawler(self.ptimer,variation=self.var)
		pword_html.send_keys(password)
		self.cprint("Typed in password")
		self.pause_crawler(self.ptimer,variation=self.var) 

		login_button = self.driver.find_element_by_class_name(button_ele)
		login_button.click()
		self.cprint("Logging in")
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	def click_send_authentication_code(self):
		send_auth_code_button=self.driver.find_element_by_class_name(
												self.resc['button_class_name'])
		send_auth_code_button.click()
		self.cprint("Clicked the (Send Authentication Code) button")
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	def get_authentication_code(self,email_un,email_pw,imap_url):
		#Keep in mind that the structure of a venmo auth code is 
		#"Your Venmo verification code is 000000" (6 numbers)
		#With Email forwarding it is: 
		#"Received SMS: Your Venmo verification code is 00000, Sender: 86753"
		#If any of that changes, we're going to have to change the program that extracts 
		#the auth number 

		#This will also BREAK/Not work if the email does not come from uchicagoamp@gmail.com
		interface = eu.email_interface(email_un,email_pw,imap_url)
		auth_emails = interface.find_emails_from(email_un)
		auth_text = interface.extract_last_email(auth_emails)
		print(auth_text)
		match = re.findall(r'verification code is \d\d\d\d\d\d',auth_text)
		if(not match):
			self.cprint("Seems to be an error with getting the auth code")
			exit()
		else:
			ac = (match[0])[-6:]
			self.cprint("Got the authentication code: {}".format(ac))
			self.pause_crawler(self.ptimer, variation=self.var)
			return ac

	def enter_authentication_code(self, code:str):
		auth_code = self.driver.find_element_by_name(self.resc['auth_html_element'])
		auth_code.send_keys(code)
		self.cprint("Entered the authentication code")
		submit_code_button = self.driver.find_element_by_class_name(self.resc['button_class_name'])
		submit_code_button.click()
		self.cprint("Clicked (Submit)")
		self.pause_crawler(self.ptimer,variation=self.var)

		buttons = self.driver.find_elements_by_class_name(self.resc['button_class_name'])
		buttons[1].click()
		self.cprint("Clicked (Not Now)")
		self.change_state(Dstate.HOME)
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	def click_href(self, relative_url):
		#this emultes a user clicking on a link rather than typing in a url
		link = self.driver.find_element_by_xpath('//a[@href="{}"]'.format(relative_url))
		self.cprint("Clicking the {} url".format(relative_url))
		link.click()
		return;

	def change_state(self, nstate):
		self.pstate = self.cstate
		self.cstate = nstate
		self.cprint("Previous state is now {}".format(self.pstate))
		self.cprint("Changing state to {}".format(nstate))
		return;

	def navigate(self,cmd,relative_url):
		switch = {
			'logout':(self.click_href,Dstate.LOGGEDOUT), #
			'home':(self.click_href,Dstate.HOME), #
			'flist':(self.click_href,Dstate.FLIST), # #friendslist
			'pprof':(self.click_href,Dstate.PERSONAL), # #personal profile
			'coprof':(self.click_href,Dstate.PROFILE), # #click other profile
			'fwd': (self.driver.forward,None),
			'back': (self.driver.back,None)
		}

		pair = switch.get(cmd, lambda: self.cprint("invalid command given\n"))
		exefunc = pair[0]
		self.cprint("Beginning Navigation: {}".format(cmd))
	
		#I don't like this approach but I think this is the only "cleanish" way to do it for now		
		if(cmd == 'fwd' or cmd == 'back'):
			self.change_state(self.pstate) 
			exefunc()
		else:
			self.change_state(pair[1])
			exefunc(relative_url)
			
		self.cprint("Done Navigating")
		self.pause_crawler(self.ptimer, variation=self.var)
		return;

	#This works, but it doesn't even matter, the users are all pre-loaded onto
	#the page
	def click_view_all(self):
		if(self.cstate != Dstate.PROFILE):
			raise ValueError("profile does not fit the choices: {}".format(valid_args))

		button = self.driver.find_element_by_partial_link_text('View All')
		button.click()
		self.cprint("clicking the (View All) button")
		return;

	def ex_users(self,fname):
		if(not (self.cstate == Dstate.FLIST or self.cstate == Dstate.PROFILE)):
			raise ValueError("Incorrect state: {}".format(self.cstate))

		usernames = []
		a = 0
		if(self.cstate == Dstate.FLIST):
			self.cprint("extracting personal profile us")
			table = self.driver.find_element_by_class_name(self.resc['personal_friendslist'])
			ihtml = table.get_attribute('innerHTML')
			page_content = BeautifulSoup(ihtml,'html.parser')
			parsed_elements = page_content.find_all("a")

			for element in parsed_elements:
				
				match = re.findall(r'[/][\w|\W]+',element.get('href'))
				if(match): #match is an empty list if there are no matches
					a = a + 1
					usernames.append(match[0])
					add_user(fname,match[0])

		else: #the two approaches to extracting friends are very different
			self.cprint("extracting other profile us")
			fs = self.driver.find_elements_by_class_name(self.resc['friend_image'])
			for nested_element in fs:
				
				user = nested_element.get_attribute(self.resc['friend_image_details'])
				match = re.findall(r'\([\w|\W]+\)',user)
				if(match):
					a = a + 1
					#indexing like this will remove the parenthesises
					temp = "/" + match[0][1:-1]
					usernames.append(temp)
					add_user(fname,temp)

			
		self.cprint(usernames)
		self.cprint("length of list = {}".format(a))
		self.cprint("done extracting")
		return;

	def ex_trans(self, fname):
		if(not (self.cstate == Dstate.PERSONAL or self.cstate == Dstate.PROFILE)):
			raise ValueError("Incorrect state: {}".format(self.cstate))

		self.expand_transaction_list()
	 
		transactions = []
		self.cprint("Beginning to extract transaction")
		raw_elements = self.driver.find_elements_by_class_name(self.resc['transaction_class'])
		# self.cprint("Length of extracted list = {}".format(len(raw_elements)))

		trns = []
		a = 0 
		for x in raw_elements:
			a = a + 1 
			# pre.append(x.get_attribute('innerHTML'))
			box_content = BeautifulSoup(x.get_attribute('innerHTML'),'html.parser')
			unames = box_content.find_all('a')
			sender = unames[0].get('href')
			recv = unames[3].get('href')
			description = (box_content.find(self.resc['desc_tag'],style=self.resc['desc_style'])).getText().strip()
			date = (box_content.find(self.resc['date_tag'],self.resc['date_class'])).getText().strip()
			privacy = "unknown"
			if(self.cstate == Dstate.PERSONAL):
				privacy = (box_content.find(self.resc['privacy_tag'],self.resc['privacy_class'])).get(self.resc['privacy_set']).strip()

			add_transaction_v2(fname,sender,recv,description,date,privacy)
			self.cprint("sender: {} recv: {} text: {} date:{} privacy:{}\n--------".format(sender,recv,description,date,privacy))
		self.cprint("Length of extracted list = {}".format(a))
		self.cprint("done extracting")
		return;

	def expand_transaction_list(self):
		if(not (self.cstate == Dstate.PROFILE or self.cstate == Dstate.PERSONAL)):
			raise ValueError("Incorrect state: {}".format(self.cstate))

		#More button: Class = moreButton "More"
		#More button: Class = moreButton "No more payments"
		expand_list = True
		while(expand_list):
			try:
				more_button = self.driver.find_element_by_link_text(self.resc['more_href'])
				more_button.click()
				self.cprint("\tPressed the (More) button")
			except selenium.common.exceptions.NoSuchElementException:
				self.cprint("There is no more (More) buttons to press")
				expand_list = False

			self.pause_crawler(self.ptimer,variation=self.var)

		# self.driver.find_element_by_xpath('//a[@href="{}"]'.format(self.resc[]))
		self.cprint("Done expanding the transactions on the profile")
		return;

	def cprint(self, p): #CPrint = Crawler Print 
		if(self.verbose):
			print(p)
			return;
		return;

	def pause_crawler(self,sec,variation=0):
		st = random.uniform(sec-variation,sec+variation)
		self.cprint("\t\tSleeping for {} secs".format(round(st,3)))
		time.sleep(st)
		self.cprint("\t\tDone sleeping")
		return; 

	def pause_crawler_v2(self):
		st = random.uniform(self.ptimer - self.var, self.ptimer + self.var)
		self.cprint("\t\tSleeping for {} secs".format(rounds(st,3)))
		time.sleep(st)
		self.cprint("\t\tDone Sleeping")
		return;

	def exit_browser(self,error_msg):
		print("Shutting down browser: {}".format(error_msg))
		self.driver.quit()

	def run(self,v_un,v_pw,email_un,email_pw,ftrnx,fusr,imap_url='imap.gmail.com'):
		# try: 
		self.open_website()
		self.login(v_un,v_pw)
		self.click_send_authentication_code()
		self.pause_crawler(10, variation = 2)
		# auth_code=self.get_authentication_code(email_un,email_pw,imap_url)
		self.pause_crawler(10, variation = 2)
		# self.enter_authentication_code(auth_code)
		
		self.pause_crawler(30,variation=0)
		self.change_state(Dstate.HOME)

		# self.navigate('pprof', self.profile) #go to person profile
		# self.pause_crawler(20, variation = 6) 
		# self.navigate('back', None) #go back to home
		# self.pause_crawler(20, variation = 6)
		# self.navigate('fwd', None) # go back forward to personal profile
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
		self.navigate('pprof', self.profile)
		self.pause_crawler(20,variation =6)
		self.ex_trans(ftrnx)
		self.navigate('flist','/friends')
		self.pause_crawler(20,variation = 3)
		self.ex_users(fusr)
		# self.navigate('coprof',"/Ted-Kim-14")
		self.navigate('coprof',"/Ranjan-Guniganti")
		self.pause_crawler(20,variation = 3)
		self.ex_users(fusr)
		self.ex_trans(ftrnx)


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
		'friends_href':'/friends',
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
	a.run(cred.v_username2,cred.v_password2,cred.v_email_un,cred.v_email_pd,'three.trnx','three.usr')
	