from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import re
import random
import cred #python file that contains venmo login information
#This is excluded from the github commit for obvious reasons

import email_utility as eu 
import privacy_utility as pu 

#un = UserName
#pw = PassWord

#To research, read Selenium's Web Driver Wait

class alpha_crawler():
	def __init__(self,pause_timer=30,var=5,verbose=True,**html_resources):
		self.ptimer = pause_timer 
		self.var = var
		self.verbose = verbose
		self.resc = html_resources
		browser_options = webdriver.ChromeOptions()
		browser_options.add_argument("--incognito")
		self.driver = webdriver.Chrome(options=browser_options)
		return;

	def open_website(self,x=0,y=0,width=500,length=900):
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
		buttons[0].click()
		self.cprint("Clicked (Remember)")
		self.pause_crawler(self.ptimer,variation=self.var)
		return;

	def cprint(self, p):
		#CPrint = Crawler Print 
		if(self.verbose):
			print(p)
			return;
		return;

	def pause_crawler(self,sec,variation=0):
		st = random.uniform(sec-variation,sec+variation)
		self.cprint("\tSleeping for {} secs".format(round(st,3)))
		time.sleep(st)
		self.cprint("\tDone sleeping")
		return; 

	def exit_browser(self,error_msg):
		print("Shutting down browser: {}".format(error_msg))
		self.driver.quit()

	def run(self,v_un,v_pw,email_un,email_pw,imap_url='imap.gmail.com'):
		self.open_website()
		self.login(v_un,v_pw)
		self.click_send_authentication_code()
		auth_code=self.get_authentication_code(email_un,email_pw,imap_url)
		self.enter_authentication_code(auth_code)


if __name__ == "__main__":
	html_info = {
		'login-url': 'https://venmo.com/account/sign-in/',
		'username_html_element':'phoneEmailUsername',
		'password_html_element':'password',
		'button_class_name':'ladda-label',
		'auth_html_element':'token'
	}
	a = alpha_crawler(pause_timer=10,var=2,verbose=True,**html_info)
	a.run(cred.v_username2,cred.v_password2,cred.v_email_un,cred.v_email_pd)