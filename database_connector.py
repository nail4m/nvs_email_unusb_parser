# encoding: utf-8

# This file is for databases

# First one is file database, just one json file

# Secondly file for mongodb



import os
import json
from logging_example import logger
import datetime

DBFILENAME = '\\unsub_db.json'
PROJECTDEVDB = os.path.dirname(os.path.realpath(__file__)) + DBFILENAME

class DB_Connector_for_unsub():
    unsub_db: dict
    def create_user(self, user_id: str):
        pass

    def get_email_list_for_user(self, user_id: str) -> list:
        pass

    def get_sorted_emails_susbscriptions(self, email: str, sort_order: str) -> dict:
        pass

    def add_email_for_user(self, user_id, email: str, **connection_data):
        pass

    def update_email_susbcriptions(self, email: str):
        pass

    def delete_user_email(self, email: str):
        pass

class DB_File_connector_for_unsub(DB_Connector_for_unsub):
    def __init__(self, db_filename: str) -> None:
        # print(db_filename)
        self.dbfile = db_filename
        if os.path.exists(db_filename):
            with open(db_filename, 'r') as f:
                logger.debug(f"DB file has been opened, filename is {db_filename}")
                self.database_json = json.load(f)
        else:
            logger.debug(f'There are no such file {self.dbfile} creating new db')
            self.database_json = dict()

    def create_user(self, user_id: str):
        if user_id in self.database_json:
            logger.warning(f'User with such id: {user_id} is already exists')
        else:
            self.database_json[user_id] = dict()

    def add_email_for_user(self, user_id, email: str, **connection_data):
        if not 'email_list' in self.database_json[user_id]:
            self.database_json[user_id]['email_list'] = list()
        if email in self.database_json[user_id]['email_list']:
            logger.warning(f'Email {email} is already in email_list')
        else:
            self.database_json[user_id]['email_list'].append(email)
        if 'emails_data' not in self.database_json:
            self.database_json['emails_data'] = dict()
        if email in self.database_json['emails_data']:
            logger.warning(f'Such email {email} is already exists in this database')
        else:
            self.database_json['emails_data'][email] = dict()
            now = datetime.datetime.now()
            self.database_json['emails_data'][email]['last_updated'] = now.isoformat()
            self.database_json['emails_data'][email]['user_id'] = user_id
        if connection_data:
            for data in connection_data:
                self.database_json['emails_data'][email][data] = connection_data[data] 
            logger.debug(f'Added new email - {email} for user {user_id}')


    def get_email_list_for_user(self, user_id: str) -> list:
        if 'email_list' in self.database_json[user_id]:
            return [email for email in self.database_json[user_id]['email_list']]
        else:
            print('There are no emails for this user, add them first')

    def get_sorted_emails_susbscriptions(self, email: str, sort_order: str) -> dict:
        sort_order_list = ['Count', 'Date']
        if sort_order not in sort_order_list:
            logger.warning('Cannot find this sort order, sorting by count as default')
            sort_order = 'Count'
        if email not in self.database_json['emails_data']:
            logger.critical(f'There are not such email in database {email}')
            return
        else:
            if sort_order == 'Count':
                sorted_subscriptions = dict()
                # print(self.database_json['emails_data'][email]['subs'])
                sorted_subscriptions_keys = sorted(self.database_json['emails_data'][email]['subs'], key=lambda subscription: self.database_json['emails_data'][email]['subs'][subscription][sort_order])
                for key in reversed(sorted_subscriptions_keys):
                    sorted_subscriptions[key] = self.database_json['emails_data'][email]['subs'][key]
            else:
                sorted_subscriptions = dict()
                sorted_subscriptions_keys = sorted(self.database_json['emails_data'][email]['subs'], key=lambda subscription: datetime.datetime.fromisoformat(self.database_json['emails_data'][email]['subs'][subscription][sort_order]))
                for key in reversed(sorted_subscriptions_keys):
                    sorted_subscriptions[key] = self.database_json['emails_data'][email]['subs'][key]
            return sorted_subscriptions

    def update_email_susbcriptions(self, email: str, new_subs: dict):
        if 'subs' in self.database_json['emails_data'][email]:
            for sub in new_subs:
                if sub in self.database_json['emails_data'][email]['subs']:
                    subs_dict = self.database_json['emails_data'][email]['subs']
                    subs_dict[sub]['Count'] += new_subs[sub]['Count']
                    if datetime.datetime.fromisoformat(subs_dict[sub]['Date']) < datetime.datetime.fromisoformat(new_subs[sub]['Date']):
                        subs_dict[sub]['Date'] = new_subs[sub]['Date']
                        subs_dict[sub]['List-Unsubscribe'] = new_subs[sub]['List-Unsubscribe']
        else:
            self.database_json['emails_data'][email]['subs'] = new_subs

    def delete_user_email(self, email: str):
        if email not in self.database_json['emails_data']:
            logger.warning(f"There are not such email, or data has been corrupted")
        else:
            deleted_elem = self.database_json['emails_data'].pop(email)
            user_id = deleted_elem['user_id']
            self.database_json[user_id].delete(email)

    def save_to_db(self):
        with open(self.dbfile, 'w') as f:
            json.dump(self.database_json, f)

    def __del__(self):
        logger.debug('DB object has been closed, saving to db')
        try:
            self.save_to_db()
            logger.debug('Save has been completed')
        except Exception as e:
            logger.critical(f'Couldn\'t save to db: {e}')