#import getpass
import datetime
from email.policy import default
import imaplib
import re
import database_connector as dbc
from typing import Dict, List
import getpass

from logging_example import logger

# Save to MongoDB email result, email datas except for pass
# Get Data from MongoDB
# Need to create some queue for parsing mails(realized function to check only messages without tags), because it could be a very long proccess and it could cause a ban from mail system
# Get pass, email and action from outside
# Get ability to 1) Add email to list of check, 2) Get Data for email 3) Update email's info 4) Delete email.
# This file must just connect and implement different connections, Other file must get data and send data to DB, delete emails and update their info,
# other must update info like this one does, other implement API functions
# Create classes not just functions
# Create interfaces
# Implement OAuth2
# Parse FROM for just an email

H_FETCHER = '(BODY[HEADER])'
USER = 'DEFAULT_USER'

SENDER_DEFAULT_DICT = {'Date': '1970-01-01T00:00:00+00:00',
                        'Count': 0,
                        'List-Unsubscribe': 'Look like it\'s empty now, but we can not be sure, thar there are no link in message'}

def get_imap_ssl_client(email_address: str, imap_server: str, imap_port: int = 993) -> imaplib.IMAP4_SSL:
    # server, port and email should, as long as connection type should be kept in db
    SERVER = imap_server
    PORT = imap_port
    logger.debug(f'Connecting to server - {SERVER}:{PORT}, email - {email_address}, with IMAP4_SSL')
    password = getpass.getpass() # should get it on front, it won't keep it
    imap_connection = imaplib.IMAP4_SSL(SERVER)
    imap_connection.login(email_address, password)
    return imap_connection

#might be oath2 imap client, imap_ssl(tls), pop3_ssl(tls), must save this data somewhere
def get_mail_client(conn_type: str, **kwargs):
    logger.debug(f'Connecting to e-mail with {conn_type}')
    if conn_type == 'imap_ssl':
        try:
            email = kwargs['email']
            server = kwargs['server']
            port = kwargs['port']
            mail = get_imap_ssl_client(email, server, port)
            return mail
        except KeyError as e:
            err_mess = f'Looks like there are not enough data to connect or credentials are incorrect: {e}'
            logger.critical(err_mess)
            raise ValueError(err_mess)
    else: 
        err_mess = 'We didn\'t write a code to connect to anything except the imap4_ssl yet'
        logger.critical(err_mess)
        raise ValueError(err_mess)


def get_messages_list(mail_con: any):
    logger.debug('Getting messages list')
    mail_con.select()
    type, message_ids = mail_con.search(None, 'NOT KEYWORD "SeenByDevUnsubPy"')

    return message_ids[0].split()

# neet to parse it somehow depends on URL or e-mail
def parse_unsub_link(unsub_header: str) -> str:
    return unsub_header

def update_unsub(unsubdict: dict, sender: str, sent_date: datetime.date, unsub_link: str):
    logger.debug(f'Updating info for email {sender}')
    if sender not in unsubdict:
        logger.debug(f'There is no record for this e-mail, creating new')
        unsubdict[sender] = SENDER_DEFAULT_DICT.copy()
    unsub_prev_date = datetime.datetime.fromisoformat(unsubdict[sender]['Date'])
    if unsub_link and unsub_prev_date < sent_date:
        logger.debug(f'New Unsub link for this email is {unsub_link}')
        unsubdict[sender]['List-Unsubscribe'] = unsub_link
        unsubdict[sender]['Date'] = sent_date.isoformat()
    unsubdict[sender]['Count'] += 1
    logger.debug(f"We counted to {unsubdict[sender]['Count']} for this e-mail")

# parse headers list and add info to set of from emails
def change_unsubdict(headers: list, unsubdict: dict):
    format_date_email = '%d %b %Y %H:%M:%S %z'
    unsub_link: str = ''
    sender = ''
    for header in headers:
        if re.match('.*: .*', header):
            name, value = header.split(': ', 1)
            if 'from' in name.lower(): 
                sender = value
            if name == 'List-Unsubscribe':
                unsub_link = parse_unsub_link(value)
            if name == 'Date':
                formated_date_match = re.match('.*?(\d{1,2} [A-Z][a-z]{2} 20[0-9]{2} \d{2}:\d{2}:\d{2} [\+-]\d+)', value)
                formated_date_match_txt = re.match('.*?(\d{1,2} [A-Z][a-z]{2} 20[0-9]{2} \d{2}:\d{2}:\d{2}) \(?[A-Z]+\)?', value)
                if formated_date_match:
                    logger.debug(f'Date is parsed as numeric timezone {value}')
                    formated_date = formated_date_match.group(1)
                elif formated_date_match_txt:
                    logger.debug(f'Date is parsed as txt timezone {value}')
                    formated_date = formated_date_match.group(1) + ' +0000'
                else:
                    logger.warning(f'Date cannot be parsed {value}')
                    formated_date = '01 Jan 1970 00:00:00 +0000'
                sent_date = datetime.datetime.strptime(formated_date, format_date_email)
    if not (sender and sent_date):
        logger.critical(f'There are no existing from or sent_date or they cannot be parsed on of element for {headers}')
    else:
        update_unsub(unsubdict, sender, sent_date, unsub_link)

def get_headers_list(mail_con: any, message_ids) -> dict:
    unsubdict = dict()
    counter = 0
    for num in message_ids:
        counter += 1
        if counter > 100:
            break
        tmp, data = mail_con.fetch(num, '(BODY.PEEK[HEADER])')
        headers = get_headers_from_fetched_data(data)
        change_unsubdict(headers, unsubdict)
        mail_con.store(num, '+FLAGS', 'SeenByDevUnsubPy')
    return unsubdict


def get_headers_from_fetched_data(fetched_data) -> list:
    for part in fetched_data:
        if isinstance(part, tuple):
            return part[1].decode().split('\r\n')

def check_auth_params(**email_auth: Dict[str]) -> dict:
    email: str = email_auth['email_address']
    server: str = email_auth['server']
    if email_auth['port']:
        try:
            email_auth['port'] = int(email_auth['port'])
        except ValueError:
            logger.critical('Port must be an int')
            SystemExit(1)
    else:
        email_auth['port'] = 993
    email_match = re.match('\w+@\w+(?:\.\w+)+', email)
    if not email_match:
        logger.critical(f'Entered e-mail has wrong format: {email}')
        SystemExit(1)
    server_match = re.match('(?i)(?:[a-z0-9][\w-]+\.)*(\w[\w-]+)')
    if not server_match:
        logger.critical(f'Entered server doesn\'t looks like a valid domain or ip: {server}')
        SystemExit(1)
        


def main():
    email_address = input('Write your e-mail address')
    imap_server = input('Your imap server like imap.gmail.com')
    imap_port = input('Your server\'s port, default is 993')
    check_auth_params(email_address=email_address, server=imap_server, port=imap_port)
    unsubdb = dbc.DB_File_connector_for_unsub(dbc.PROJECTDEVDB)
    global SENDER_DEFAULT_DICT
    mail = get_mail_client('imap_ssl', email = email_address, port = imap_port, server = imap_server)
    messages_ids = get_messages_list(mail)
    unsubdict = get_headers_list(mail, messages_ids)
    unsubdb.update_email_susbcriptions(email_address, unsubdict)
    

if __name__ == '__main__':
    main()
