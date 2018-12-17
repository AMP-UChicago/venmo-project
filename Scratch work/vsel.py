import os 
import sys 
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import cred #python file that contains venmo login information
#This is excluded from the github commit for obvious reasons (lol)

if __name__ == "__main__":
	driver = webdriver.Chrome()
	driver.get("https://venmo.com/account/sign-in/")

	driver.set_window_size(900,900)
	driver.set_window_position(0,0)
	print("resized windows")

	# a = driver.find_elements_by_class_name("auth-form-input")
	# username = a[0]
	# password = a[1]
	username = driver.find_element_by_name("phoneEmailUsername")
	password = driver.find_element_by_name("password")
	username.send_keys(cred.username)
	password.send_keys(cred.password)
	print("inserted stuff")

	button = driver.find_element_by_class_name("ladda-label")
	button.click()

	print("Sleeping")
	time.sleep(30)
	print("Done Sleeping")

	button_send_code = driver.find_element_by_class_name("ladda-label")
	button_send_code.click()

	print("sleeping")
	time.sleep(30)
	print("Done Sleeping")
	auth_code = driver.find_element_by_name("token")
	auth_code.send_keys("00000000")

	button_submit_code = driver.find_element_by_class_name("ladda-label")
	button_submit_code.click()

	print("Sleeping")
	time.sleep(30)
	print("Done sleeping")
	b = driver.find_elements_by_class_name("ladda-label")
	b[0].click()