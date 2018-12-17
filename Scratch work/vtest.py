import requests 
import json 
from bs4 import BeautifulSoup
import cred #python file that contains venmo login information
#This is excluded from the github commit for obvious reasons (lol)


# /account/login, method post

#Network information 
# venmo.com/login
# Then 
# venmo.com/account/login

# token thing = 7VoLfr6kpHi1G9uj8osBwmQ11bv55XZV
# token changes every time 

# input type = "text"
# class = "auth-form-input"
# aria-label = "username"
# value = ""

# input type = "password"
# class = "auth-form-input"
# aria-label = "password"
# value = ""

# input.auth-form-input
def simple_get(url):
	r = requests.get(url)
	print(r.status_code) #200 means success
	print(r.headers['content-type'])
	print(r.encoding)
	ppf = r.text
	pretty = BeautifulSoup(ppf, features = "html5lib")
	print(pretty.prettify())
	# print(r.text)
	# print(r.json())

def login_one(url):

	headers = {
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
	}

	payload = {
		'phoneEmailUsername':cred.username,
		'password': cred.password
	}

	session = requests.Session()
	session.get(url, headers = headers)
	
	resp = session.post("https://venmo.com", data=payload)
	print(resp.status_code)
	ppf = resp.text
	pretty = BeautifulSoup(ppf,features = "html5lib")
	print(pretty.prettify())

def login_two(url):
	headers = {
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
	}

	payload = {
		'phoneEmailUsername':cred.username,
		'return_json':'true',
		'password':cred.password
	}

	session = requests.Session()
	session.get("https://venmo.com", headers = headers)
	
	resp = session.post(url, data=payload)
	print(resp.status_code)
	ppf = resp.text
	pretty = BeautifulSoup(ppf,features = "html5lib")
	print(pretty.prettify())

if __name__ == "__main__":
	vurl = "https://venmo.com/login"
	vurl2 = "https://venmo.com/account/login"
	# vurl3 = "https://venmo.com/account/sign-in" #definitely does not work 
	# simple_get(vurl)	
	# login_one(vurl)
	# login_one(vurl2)
	# login_two(vurl) #error 400, not enough authentication
	# login_two(vurl2) #205, wron fuser name and passwd
