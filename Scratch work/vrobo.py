import re 
from robobrowser import RoboBrowser
import cred #python file that contains venmo login information
#This is excluded from the github commit for obvious reasons (lol)

if __name__ == "__main__":
	url = "https://venmo.com/account/sign-in"
	ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
	br = RoboBrowser(parser = "html5lib", user_agent = ua)
	br.open(url) 
	form = br.get_form(class_="auth-form")
	form["phoneEmailUsername"] = cred.username
	form["password"] = cred.password
	br.submit_form(form)

	print(br.response)
	print(br.url)
	print(br.parsed)

