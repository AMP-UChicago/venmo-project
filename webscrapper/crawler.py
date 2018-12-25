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
class Cstate(Enum):
	LOGIN = 1 
	HOME = 2
	PERSONAL = 3
	FRIENDSLIST = 4
	PROFILE = 5
	LOGGEDOUT = 6

#class = "connection-username" data-reacid = ""
#Usernames on profiles are covered in parenthesis ex: (username here)

#in addition, when you open up the friend's page of a different user, you cannot 
#actually see all of them like you do for your personal friends, just a list of images

#on a stranger's profile, there seems to be multiple "small" class = "small" button
#only one view all is on each profle
class alpha_crawler():
	def __init__(self,prof_un,pause_timer=30,var=5,verbose=True,**html_resources):
		self.state = Cstate.LOGIN
		self.profile = prof_un
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
		interface = eu.email_interface(email_un,email_pw,imap_url)
		auth_emails = interface.find_emails_from(email_un)
		auth_text = interface.extract_last_email(auth_emails)

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
		self.state = Cstate.HOME #Right after you log in, you should be on the home screen
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	def click_href(self, relative_url):
		link = self.driver.find_element_by_xpath(
										'//a[@href="{}"]'.format(relative_url))
		self.cprint("Clicking the {} url".format(relative_url))
		link.click()

	#TODO Condense these functions to make it more elegant
	def logout(self):
		self.click_href("/account/logout")
		self.state = Cstate.LOGGEDOUT
		self.pause_crawler(self.ptimer,variation=self.var)
		# lb = self.driver.find_element_by_xpath('//a[@href="'+ "/account/logout"+ '"]')
		# print(lb)
		# lb.click()

	def perfriendslist(self):
		self.click_href("/friends")
		self.state = Cstate.FRIENDSLIST
		self.cprint("Clicked the (friends) link: switched to FRIENDS state")
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	def home(self):
		self.click_href("/")
		self.state = Cstate.HOME
		self.cprint("Clicked the (home) link: switch to HOME state")
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	def perprofile(self):
		self.click_href("/" + self.profile)
		self.current_profile = ""
		self.state = Cstate.PERSONAL
		self.cprint("Clicked the (user's profile) link: switch to PROFILE")
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	def click_profile(self, username):
		self.click_href("/" + username)
		self.current_profile = username
		self.state = Cstaste.PROFILE

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

	#extracts friends from a different profile 
	def extract_users(self):
		users = self.driver.find_elements_by_class_name('anchor')
		usernames = []
		for x in users:
			users = x.get_attribute('details')
			match = re.findall(r'\([\w|\W]+\)',users)
			if(match):
				# print(match[0][1:-1]) #indexing removes the parenthesises
				temp = "/" + match[0][1:-1]
				print(temp)
				usernames.append(temp)

		print(usernames)
		print(len(users))
		print(len(usernames))
		return usernames

	#Extracts the personal profile's friends
	#Also gets the proper number of friends 
	def extract_friends(self):
		table = self.driver.find_element_by_class_name('settings-people-members')
		a = table.get_attribute('innerHTML')
		
		page_content = BeautifulSoup(a,"html.parser")
		tags = page_content.find_all("a")
		# there are a lot of junk URLs on the page
		newlist = []
		for x in tags: 
			# print(x) #Prints an href object
			# print(x.get('href')) #prints # of the username
			# newlist.append(x.get('href'))
			match = re.findall(r'[/][\w|\W]+',x.get('href'))
			if(match): #If the list is non-empty
				newlist.append(match[0])
			
		print(newlist)
		# print(len(newlist))
		return;

#--------------------------------------------------------------------------------
	#This Works
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
		self.open_website()
		self.login(v_un,v_pw)
		self.click_send_authentication_code()
		# auth_code=self.get_authentication_code(email_un,email_pw,imap_url)
		# self.enter_authentication_code(auth_code)
		self.pause_crawler(30,variation=0)
		# self.pause_crawler(10,variation=0)	
		# self.perfriendslist()
		# self.home()
		self.perfriendslist()	
		self.extract_friends()
		# self.home()
		# self.perprofile()
		# self.cprint("Fucking d o it right now")
		# self.pause_crawler(30,variation=0)
		# self.click_view_all() # we don't actually need to click view_all
		# self.extract_users()
		# self.expand_transaction_list()
		# self.logout()


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
		'no_more_payments_href':'No more payments'
	}
	a = alpha_crawler(cred.v_prof,pause_timer=5,var=1,verbose=True,**html_info)
	a.run(cred.v_username2,cred.v_password2,cred.v_email_un,cred.v_email_pd)