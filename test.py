# encoding: utf-8
import database_connector as dbc

new_fdb = dbc.DB_File_connector_for_unsub(dbc.PROJECTDEVDB)

# new_fdb.create_user('test')


#new_fdb.add_email_for_user('test', 'nail10224@gmail.com', conn_type = 'imap_ssl', imap_server = 'imap.gmail.com', imap_port = 993)
email_list = new_fdb.get_email_list_for_user('test')



sorted_list = new_fdb.get_sorted_emails_susbscriptions('nail10224@gmail.com', 'Date')
print(sorted_list)
# print(email_list)
#print(new_fdb.database_json)

