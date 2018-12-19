#Library used to help access email
import imaplib
import email
import os
import cred 

#todo make sure it's able to read properly search and sort through the emails

def extract_emails(byte_data):
	msgs = []
	for num in byte_data[0].split():
		ty, data = con.fetch(num,'(RFC822)')
		msgs.append(data)
	return msgs



class email_authenticator():
	def __init__(self,username,password,imap_url):
		self.connection = imaplib.IMAP4_SSL(imap_url)
		self.connection.login(username,password)

	def search_email(self,key,value):
		
		



if __name__ == "__main__":
	username = cred.email_un 
	password = cred.email_pd