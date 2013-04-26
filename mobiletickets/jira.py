import json
import requests
import lxml.html
from mobiletickets import app


class JiraClient(object):
    def __init__(self, session_id=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': "MobileTickets/0.1",
            'Content-Type': "application/json",
            'Accept': "application/json",
            })
        self.session.verify = False # FIXME

        if session_id:
            self.session.cookies.update({'JSESSIONID': session_id})

    def get(self, path, data=None):
        if data:
            data = json.dumps(data)

        r = self.session.get(app.config['JIRA_API'] + '/' + path, data=data)
        return json.loads(r.text)


    def post(self, path, data=None):
        if data:
            data = json.dumps(data)

        r = self.session.post(app.config['JIRA_API'] + '/' + path, data=data)
        return json.loads(r.text)

    def issue(self, key):
        data = self.get('api/latest/issue/' + key)
        return Issue(data)


class Issue(object):
    def __init__(self, data):
        self.key = data[u'key']
        self.url = data[u'self']
        for k, v in data[u'fields'].items():
            if u'value' in v:
                setattr(self, k, v[u'value'])

    def __repr__(self):
        return "<Issue: {key}>".format(key=self.key)
