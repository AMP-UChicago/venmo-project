from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import re
import random
import cred #python file that contains venmo login information
#This is excluded from the github commit for obvious reasons

import email_utility as eu 


class venmo_crawler():
	def __init__(self,username,password,email_un,email_pw,verbose=True,**html_resources):
		self.verbose = verbose
		self.email_un = email_un
		self.email_pw = email_pw
		self.resc = html_resources

		option = webdriver.ChromeOptions()
		option.add_argument("--incognito")
		self.driver = webdriver.Chrome(options=option)

		self.open_website()
		self.login(username,password)
		# open_website(self.driver, self.resc['login-url'])
		# login(self.driver, username, password,**self.resc)
		self.click_send_authentication_code()
		auth_code = self.get_authentication_code()
		self.enter_authentication_code(auth_code)

	def open_website(self, x=0,y=0,width=900,length=900):
		self.driver.get(self.resc['login-url'])
		self.driver.set_window_size(width,length)
		self.driver.set_window_position(x,y)
		print("Opening website")
		self.pause_crawler(7,variation=2,verbose=self.verbose)
		return;

	def login(self,username,password):
		uname_ele = self.resc['username_name_element']
		pword_ele = self.resc['password_name_element']
		button_ele = self.resc['button_name_element']

		uname_html = self.driver.find_element_by_name(uname_ele)
		pword_html = self.driver.find_element_by_name(pword_ele)
		uname_html.send_keys(username)
		self.pause_crawler(5,variation=1,verbose=self.verbose)
		pword_html.send_keys(password)
		self.pause_crawler(5,variation=1,verbose=self.verbose) #necessary to prevent a "Too many REquests error"

		login_button = self.driver.find_element_by_class_name(button_ele)
		login_button.click()
		print("Logging in")
		self.pause_crawler(10,variation=2,verbose=self.verbose)
		return;

	def click_send_authentication_code(self):
		button_send_code = self.driver.find_element_by_class_name(
											self.resc['button_name_element'])
		button_send_code.click()
		print("clicked the 'Send authentication code'")
		self.pause_crawler(10,variation=2,verbose=self.verbose)
		return;

	def get_authentication_code(self):
		#Keep in mind that the structure of a venmo auth code is 
		#"Your Venmo verification code is 000000" (6 numbers)
		#With Email forwarding it is: 
		#"Received SMS: Your Venmo verification code is 00000, Sender: 86753"
		#If any of that changes, we're going to have to change the program that extracts 
		#the auth number 
		interface = eu.email_interface(self.email_un, self.email_pw, 'imap.gmail.com')
		auth_emails = interface.find_emails_from(self.email_un)
		auth_text = interface.extract_last_email(auth_emails)

		match = re.findall(r'verification code is \d\d\d\d\d\d',auth_text)
		if(not match):
			exit()
		else:
			return (match[0])[-6:]
			self.pause_crawler(15,variation=3,verbose=self.verbose)

	def enter_authentication_code(self, code:str):
		auth_code = self.driver.find_element_by_name(self.resc['auth-code'])
		auth_code.send_keys(code)
		# auth_code.send_keys("{}".format(code)) #this was when code was set to an int

		button_submit_auth = self.driver.find_element_by_class_name(
										self.resc['button_name_element'])
		button_submit_auth.click()
		
		self.pause_crawler(20,variation=5,verbose=self.verbose)
		button_remember_me = self.driver.find_elements_by_class_name(
										self.resc['button_name_element'])
		button_remember_me[0].click()
		self.pause_crawler(10,variation=2,verbose=self.verbose)
		return;


	def pause_crawler(self,sec,variation=0,verbose=True):
		st = random.uniform(sec-variation,sec+variation)
		if(verbose):
			print("Sleeping for {}".format(int(st)))
			time.sleep(st)
			print("Done sleeping")
			return;
		time.sleep(st)

if __name__ == "__main__":
	html_info = {
		'login-url': 'https://venmo.com/account/sign-in/',
		'username_name_element':'phoneEmailUsername',
		'password_name_element':'password',
		'button_name_element':'ladda-label',
		'auth-code':'token'
	}
	a = venmo_crawler(cred.v_username2,cred.v_password2,cred.v_email_un,
												cred.v_email_pd,**html_info)