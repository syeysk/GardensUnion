import requests
from gi.repository import Gtk
from sqlalchemy import update

from db import Contact


class TGAdapter:
    token = ''#os.getenv('TG_TOKEN')

    def __init__(self, adapter_area, get_contact, session):
        self.get_contact = get_contact
        self.session = session
        self.url = f'https://api.telegram.org/bot{self.token}'

        # init GUI
        button_get_id = Gtk.Button(label='get id')
        button_get_id.connect('clicked',self.action_get_user_id)
        adapter_area.append(button_get_id)

        button_fix = Gtk.Button(label='fix')
        button_fix.connect('clicked',self.action_fix)
        adapter_area.append(button_fix)

        button_update = Gtk.Button(label='update')
        button_update.connect('clicked',self.action_update_username)
        adapter_area.append(button_update)

    @staticmethod
    def link2username(link):
        if link.startswith('@'):
            return link
    
        chat_name = link
        if link.startswith('https://t.me/') or link.startswith('t.me/'):
            chat_name = link.split('/')[-1]

        return f'@{chat_name}'

    def load_numeric_id(self, username):
        params = {'chat_id': username}
        response = requests.post(f'{self.url}/getChat', json=params)
        if response.status_code == 200:
            response_json = response.json()
            if response_json.get('ok'):
                result = response_json['result']
                return result['id']

    def load_username(self, userid):
        params = {'chat_id': userid}
        response = requests.post(f'{self.url}/getChat', json=params)
        if response.status_code == 200:
            response_json = response.json()
            if response_json.get('ok'):
                result = response_json['result']
                return result['username']

    def action_get_user_id(self, _):
        contact = self.get_contact()
        if contact:
            data = contact.data
            existing_userid = data.get('userid')
            if not existing_userid:
                username = self.link2username(contact.value)
                userid = self.load_numeric_id(username)
                if userid:
                    data['userid'] = userid
                    self.session.execute(update(Contact).where(Contact.id == contact.id).values(data=data))
                    self.session.commit()

    def action_fix(self, _):
        contact = self.get_contact()
        if contact:
            username = self.link2username(contact.value)
            contact.value = username[1:]
            self.session.commit()

    def action_update_username(self, _):
        contact = self.get_contact()
        if contact:
            data = contact.data
            existing_userid = data.get('userid')
            if existing_userid:
                username = self.load_username(existing_userid)
                if username and contact.value != username:
                    previous_usernames = data.setdefault('previous_usernames', [])
                    if contact.value not in previous_usernames:
                        previous_usernames.append(contact.value)
                        self.session.execute(update(Contact).where(Contact.id == contact.id).values(data=data))

                    contact.value = username[1:]
                    self.session.commit()