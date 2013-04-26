from flask import abort, redirect, render_template, Response, session, url_for
from mobiletickets import app
from mobiletickets import jira


# TODO: remove this and replace it with real login
jc = jira.JiraClient(app.config['SESSION_ID'])


@app.route('/')
def index():
    result = jc.post('search', {
        'jql': "project = MT",
        'startAt': 0,
        'maxResults': 15,
        })
    if not 'issues' in result:
        abort(result[u'status-code'])

    issues = []
    for item in result['issues']:
        issue = jc.issue(item['key'])
        issues.append(issue)
    return render_template('index.html', issues=issues)


@app.route('/issue/<string:key>')
def issue(key):
    issue = jc.issue(key)
    return render_template('ticketview.html', issue=issue)


@app.route('/issue/new')
def newissue():
    return render_template('newticket.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')
