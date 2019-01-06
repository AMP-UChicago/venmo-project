#Library used to help access email
#This library Definitely needs a good fix up/reorganization 
import imaplib
import email
import os
import re
import cred
import smtplib
import ssl

# TODO = Implement Unit tests for email utility
#Also include type hints, because I don't really get what's happening 

def get_email_body(msg):
	if msg.is_multipart():
		return get_email_body(msg.get_payload(0))
	else: 
		return (msg.get_payload(None,True)).decode('utf-8')

def format_email(saddr,raddr,subj,message):
	eml = email.message.EmailMessage()
	eml['Subject'] = subj
	eml['From'] = saddr	
	eml['To'] = raddr
	eml.set_content(message)
	return eml

#stolen from a tutorial online
def send_email(email_server,saddr,raddr,pw,subj,msg):
	context = ssl.create_default_context()
	# with smtplib.SMTP_SSL(email_server, 465, context=context) as server:
	server = smtplib.SMTP_SSL(email_server, 465, context=context)
	server.login(saddr,pw)
	server.sendmail(saddr,raddr,(format_email(saddr,raddr,subj,msg)).as_string())
	print("Sent email with message: {}".format(msg))


class email_interface():
	def __init__(self,username,password,imap_url,section='INBOX'):
		self.connection = imaplib.IMAP4_SSL(imap_url)
		self.connection.login(username,password)
		self.connection.select(section,readonly = True)

	#return a search key the interface uses to filter emails 
	def search_email(self,key,key_value):
		result,data = self.connection.search(None,key,'"{}"'.format(key_value))
		return data

	def extract_emails(self,result_bytes):
		msgs = []
		for num in result_bytes[0].split():
			typ, data = self.connection.fetch(num, '(RFC822)')
			msgs.append(data)
		return msgs

	#returns a list of raw byte emails, oldest = on the beginning of the list
	def find_emails_from(self, from_user):
		ser_keys = self.search_email('FROM',from_user)
		messages = self.extract_emails(ser_keys)
		return messages

	def shutdown(self):
		print("Logging out")
		resp = self.connection.logout()
		if(resp[0] != 'BYE'):
			print("Failed to logout")
		else:
			print("Logged Out Success: {}".format(resp))

	def extract_last_email(self, messages: list):
		#very specific function for the sel_crawler.py, lol
		#it's one line so sort of useless, but makes the code in sel_crawler cleaner
		# still maybe we should delete this
		return get_email_body(email.message_from_bytes((messages[-1])[0][1]))

def unit_testing():
	return


if __name__ == "__main__":
	username = cred.v_email_un 
	password = cred.v_email_pd
	test2 = ["tedkim97@uchicago.edu", "tedkim97@gmail.com"]
	send_email('smtp.gmail.com',username,test2,password,"error","hihi test message 2")
	# a = email_interface(username,password,'imap.gmail.com')
	# messages = a.find_emails_from('uchicagoamp@gmail.com')
	# print(a.extract_last_email(messages)) 