from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import cred #python file that contains venmo login information
#This is excluded from the github commit for obvious reasons

def open_website(driv_arg,url,x=0,y=0,width=900,length=900):
	driv_arg.get(url)
	driv_arg.set_window_size(width,length)
	driv_arg.set_window_position(x,y)
		
def login(driv_arg,username,password,**html_resc):
	uname_ele = html_resc['username_name_element']
	pword_ele = html_resc['password_name_element']
	button_ele = html_resc['button_name_element']

	unname_html = driv_arg.find_elements_by_class_name(uname_ele)
	pword_html = driv_arg.find_element_by_name(pword_ele)
	uname_html.send_keys(username)
	pword_html.send_keys(password)

	login_button = driv_arg.find_elements_by_class_name(button_ele)
	login_button.click()

class venmo_crawler():
	def __init__(self,username,password,**html_resources):
		self.resc = html_resources
		self.driver = webdriver.Chrome()
		open_website(self.driver, self.resc['login-url'])
		login(self.driver, username, password)

	def send_authentication_code(self):
		

	def pause_crawler(sec, verbose= True):
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
		'button_name_element':'ladda-label'
	}
	a = venmo_crawler(cred.username,cred.password,**html_info)