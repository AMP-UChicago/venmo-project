from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import cred #python file that contains venmo login information
#This is excluded from the github commit for obvious reasons

class venmo_crawler():
	def __init__(self,username,password,**html_resources):
		self.resc = html_resources
		self.driver = webdriver.Chrome()
		self.open_website()
		self.login(username,password)
		# open_website(self.driver, self.resc['login-url'])
		# login(self.driver, username, password,**self.resc)
		self.click_send_authentication_code()
		self.enter_authentication_code(123456)

	def open_website(self, x=0,y=0,width=900,length=900):
		self.driver.get(self.resc['login-url'])
		self.driver.set_window_size(width,length)
		self.driver.set_window_position(x,y)
		print("Opening website")
		self.pause_crawler(5)
		return;

	def login(self,username,password):
		uname_ele = self.resc['username_name_element']
		pword_ele = self.resc['password_name_element']
		button_ele = self.resc['button_name_element']

		uname_html = self.driver.find_element_by_name(uname_ele)
		pword_html = self.driver.find_element_by_name(pword_ele)
		uname_html.send_keys(username)
		pword_html.send_keys(password)

		login_button = self.driver.find_element_by_class_name(button_ele)
		login_button.click()
		print("Logging in")
		self.pause_crawler(10)
		return;

	def click_send_authentication_code(self):
		button_send_code = self.driver.find_element_by_class_name(
											self.resc['button_name_element'])
		button_send_code.click()
		print("clicked the 'Send authentication code'")
		self.pause_crawler(10)
		return;

	def enter_authentication_code(self, code:int):
		auth_code = self.driver.find_element_by_name(self.resc['auth-code'])
		auth_code.send_keys("{}".format(code))

		button_submit_auth = self.driver.find_element_by_class_name(
										self.resc['button_name_element'])
		button_submit_auth.click()
		
		self.pause_crawler(20)
		button_remember_me = self.driver.find_elements_by_class_name(
										self.resc['button_name_element'])
		button_remember_me[0].click()
		self.pause_crawler(10)
		return;


	def pause_crawler(self,sec, verbose= True):
		if(verbose):
			print("Sleeping for {}".format(sec))
			time.sleep(sec)
			print("Done sleeping")
			return;
		time.sleep(sec)

if __name__ == "__main__":
	html_info = {
		'login-url': 'https://venmo.com/account/sign-in/',
		'username_name_element':'phoneEmailUsername',
		'password_name_element':'password',
		'button_name_element':'ladda-label',
		'auth-code':'token'
	}
	a = venmo_crawler(cred.username,cred.password,**html_info)