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

#un = UserName
#pw = PassWord

#To research, read Selenium's Web Driver Wait

# TODO: Actually implement the CStates for the selenium driver
# TODO: Beging writing down the usernames for the thing 
# TODO: Implement better naming schemes 

#class = "connection-username" data-reacid = ""
#Usernames on profiles are covered in parenthesis ex: (username here)

#in addition, when you open up the friend's page of a different user, you cannot 
#actually see all of them like you do for your personal friends, just a list of images

#on a stranger's profile, there seems to be multiple "small" class = "small" button
#only one view all is on each profle

#Make ure that the transactions we scrape are PUBLIC

class Cstate(Enum):
	LOGIN = 1 
	HOME = 2
	PERSONAL = 3
	FRIENDSLIST = 4
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

class alpha_crawler():
	def __init__(self,prof_un,pause_timer=30,var=5,verbose=True,**html_resources):
		# self.state = Cstate.LOGIN
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
		auth_code = self.driver.find_element_by_name(
												self.resc['auth_html_element'])
		auth_code.send_keys(code)
		self.cprint("Entered the authentication code")
		submit_code_button = self.driver.find_element_by_class_name(
										self.resc['button_class_name'])
		submit_code_button.click()
		self.cprint("Clicked (Submit)")
		self.pause_crawler(self.ptimer,variation=self.var)

		buttons = self.driver.find_elements_by_class_name(
											self.resc['button_class_name'])
		buttons[1].click()
		self.cprint("Clicked (Not Now)") #I think this is what they used
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	def click_href(self, relative_url):
		#this emultes a user clicking on a link rather than typing in a url
		link = self.driver.find_element_by_xpath(
										'//a[@href="{}"]'.format(relative_url))
		self.cprint("Clicking the {} url".format(relative_url))
		link.click()

	def navigate(self,cmd,relative_url):
		switch = {
			'logout':self.click_href,
			'home':self.click_href,
			'flist':self.click_href, #friendslist
			'pprof':self.click_href, #personal profile
			'coprof':self.click_href, #click other profile
			'fwd': self.driver.forward, #forward
			'back': self.driver.back #back
		}

		exe = switch.get(cmd, lambda: self.cprint("invalid command given\b"))

		
		self.cprint("beginning navigation: {}".format(cmd))
	
		#I don't like this approach but I think this is the only "cleanish"
		#way to do it for now		
		if(cmd == 'fwd' or cmd == 'back'):
			exe()
		else: 
			exe(relative_url)

		self.cprint("done navigating")
		self.pause_crawler(self.ptimer, variation=self.var)
		return;

	#This works, but it doesn't even matter, the users are all pre-loaded onto
	#the page
	def click_view_all(self):
		# if(self.state != Cstate.PROFILE):
			# self.logout()
			# exit()
		button = self.driver.find_element_by_partial_link_text('View All')
		button.click()
		self.cprint("clicking the (View All) button")
		return;


	def ex_users(self, state):
		valid_args = {'personal','other'}
		if state not in valid_args:
			raise ValueError("profile does not fit the choices: {}".format(valid_args))

		usernames = []

		if(state == 'personal'): #this part works fine
			self.cprint("extracting personal profile friends")
			table = self.driver.find_element_by_class_name(self.resc['personal_friendslist'])
			ihtml = table.get_attribute('innerHTML')
			page_content = BeautifulSoup(ihtml,'html.parser')
			parsed_elements = page_content.find_all("a")

			for element in parsed_elements:
				match = re.findall(r'[/][\w|\W]+',element.get('href'))
				if(match): #match is an empty list if there are no matches
					usernames.append(match[0])

		else: #the two approaches to extracting friends are very different
			self.cprint("extracting other profile")
			fs = self.driver.find_elements_by_class_name(self.resc['friend_image'])
			
			for nested_element in fs:
				user = nested_element.get_attribute(self.resc['friend_image_details'])
				match = re.findall(r'\([\w|\W]+\)',user)
				if(match):
					# print(match[0][1:-1]) #indexing like this will remove the parenthesises
					temp = "/" + match[0][1:-1]
					usernames.append(temp)
			
		print(usernames)
		print(len(usernames))
		self.cprint("done extracting")
		return;

	#extracting transactions should be the same regardless of the page 
	#seems to detect 5 more than it should
	def ex_trans(self): 
		transactions = []
		self.cprint("beginngin to extract transaction")
		raw_elements = self.driver.find_elements_by_class_name(self.resc['transaction_class'])
		# print(raw_elements)
		print(len(raw_elements))

		pre = []
		for x in raw_elements: 
			# pre.append(x.get_attribute('innerHTML'))
			box_content = BeautifulSoup(x.get_attribute('innerHTML'),'html.parser')
			unames = box_content.find_all('a')
			sender = unames[0].get('href')
			recv = unames[3].get('href')
			description = (box_content.find('div',style='word-wrap:break-word')).getText().strip()
			date = (box_content.find('a','gray_link')).getText().strip()
			rpriv = (box_content.find('div',"tooltip")).getText().strip()
			print(rpriv)
			match = re.findall(r'Setting: \w+',rpriv)
			if(match):
				# print("have a match")
				privacy = match[0][8:]
			print("sender: {} recv: {} text: {} date:{} privacy:{}\n--------".format(sender,recv,description,date,privacy))
		
		# pre2 = []
		# for y in pre: 
		# 	box_content = BeautifulSoup(y, 'html.parser') #.prettify()
		# 	# tags = box_content.find_all('a')
		# 	# sender = tags[0].get('href')
		# 	# recv = tags[3].get('href')
		# 	pre2.append(box_content)
		# 	# trans = box_content.find_all('a')
		# 	# sender = trans[0].get('href')
		# 	# recv = trans[3].get('href')


		# # print(pre)
		# print(len(pre))
		# print(len(pre2))

		# jank = pre2[0].find_all('a')
		# print(jank[0].get('href'))
		# print(jank[3].get('href'))
		# #this doesn't work 
		# jank2 = pre2[0].find('div',style = 'word-wrap:break-word')
		# print(jank2)
		# print(jank2.getText().strip())

		# jank3 = pre2[0].find('a','gray_link')
		# print(jank3)
		# print(jank3.getText().strip())

		# jank4 = pre2[0].find('div',"tooltip")
		# print(jank4)
		# print(jank4.getText().strip())
		# #------------------------------------------------
		# jank5 = pre2[1].find_all('a')
		# print(jank5[0].get('href'))
		# print(jank5[3].get('href'))

		# jank6 = pre2[1].find('div',style = 'word-wrap:break-word')
		# print(jank6)
		# print(jank6.getText().strip())

		# jank7 = pre2[1].find('a','gray_link')
		# print(jank7)
		# print(jank7.getText().strip())

		# jank8 = pre2[1].find('div',"tooltip")
		# print(jank8)
		# print(jank8.getText().strip())
		# print(pre2[1].prettify())
#--------------------------------------------------------------------------------
	#This Works -  not sure if this is going to be needed
	def expand_transaction_list(self):
		# if(!(self.state == Cstate.PROFILE or self.state == Cstate.PERSONAL)):
		# 	self.pause_crawler(120,variation=0)
		# 	self.exit_browser("Crawler is not in the proper state")

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

	def run(self,v_un,v_pw,email_un,email_pw,imap_url='imap.gmail.com'):
		# try: 
		self.open_website()
		self.login(v_un,v_pw)
		self.click_send_authentication_code()
		self.pause_crawler(10, variation = 2)
		auth_code=self.get_authentication_code(email_un,email_pw,imap_url)
		self.pause_crawler(10, variation = 2)
		self.enter_authentication_code(auth_code)
		self.pause_crawler(30,variation=0)

		self.navigate('pprof', self.profile)
		self.pause_crawler(20,variation =6)
		self.expand_transaction_list()
		self.ex_trans()
#-------------------------------------------------------------------------------			
			# self.navigate('pprof', self.profile) #go to person profile
			# self.pause_crawler(20, variation = 6) 
			# self.navigate('back', "nothing") #go back to home
			# self.pause_crawler(20, variation = 6)
			# self.navigate('fwd', "aoidj") # go back forward to personal profile
			# self.pause_crawler(20, variation = 6)
			# self.navigate('pprof', self.profile) #go bacl to home
			# self.pause_crawler(20, variation = 6)
			# self.navigate('home', "/")		
			# self.pause_crawler(20, variation = 6)
			# self.navigate('back', "nothing") #go back to pprof
			# self.pause_crawler(20, variation = 6)
			# self.navigate('flist', "/friends")
			# self.pause_crawler(20, variation = 6)
			# self.navigate('logout',"/account/logout")
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
		'transaction_class': 'profile_feed_story' #'p_ten_t'
		#profile feed stories tend to work a lot better for extracting transaction
	}
	a = alpha_crawler(cred.v_prof,pause_timer=5,var=1,verbose=True,**html_info)
	a.run(cred.v_username2,cred.v_password2,cred.v_email_un,cred.v_email_pd)
	