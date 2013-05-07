from flask import abort, redirect, render_template, Response, request, \
        session, url_for
from mobiletickets import app
from mobiletickets import jira


jc = jira.JiraClient()

@app.before_request
def set_session():
    if 'JSESSIONID' in session:
        jc.set_session(session['JSESSIONID'])


@app.route('/')
@app.route('/index/<int:page>')
def index(start=0):
    user = jc.get('auth/latest/session')
    if 'status-code' in user and user['status-code'] == 401:
        abort(401)

    result = jc.post('api/latest/search', {
        'jql': 'assignee = "{user}"'.format(user=user['name']),
        'startAt': start,
        'maxResults': app.config['ISSUES_PER_PAGE'],
    })
    if u'status-code' in result:
        abort(result[u'status-code'])

    issues = []
    if 'issues' in result:
        for item in result['issues']:
            issue = jc.issue(item['key'])
            issues.append(issue)

    # pagination
    if start > 0:
        start_prev = start - app.config['ISSUES_PER_PAGE']
        if start_prev < 0:
            start_prev = 0
    else:
        start_prev = -1
    if start + app.config['ISSUES_PER_PAGE'] < result['total']:
        start_next = start + app.config['ISSUES_PER_PAGE']
    else:
        start_next = -1

    return render_template('index.html', user=user, issues=issues,
            start_prev=start_prev, start_next=start_next)


@app.route('/progress')
@app.route('/index/<int:start>')
def progress(start=0):
    user = jc.get('auth/latest/session')
    if 'status-code' in user and user['status-code'] == 401:
        abort(401)

    result = jc.post('api/latest/search', {
        'jql': 'status = "In Progress"',
        'startAt': start,
        'maxResults': app.config['ISSUES_PER_PAGE'],
    })
    if u'status-code' in result:
        abort(result[u'status-code'])

    issues = []
    if 'issues' in result:
        for item in result['issues']:
            issue = jc.issue(item['key'])
            issues.append(issue)

    # pagination
    if start > 0:
        start_prev = start - app.config['ISSUES_PER_PAGE']
        if start_prev < 0:
            start_prev = 0
    else:
        start_prev = -1
    if start + app.config['ISSUES_PER_PAGE'] < result['total']:
        start_next = start + app.config['ISSUES_PER_PAGE']
    else:
        start_next = -1

    return render_template('progress.html', user=user, issues=issues,
            start_prev=start_prev, start_next=start_next)


@app.route('/issue/<string:key>', methods=['GET', 'POST'])
def issue(key):
    user = jc.get('auth/latest/session')
    if 'status-code' in user and user['status-code'] == 401:
        abort(401)

    try:
        issue = jc.issue(key)
    except (KeyError, ValueError):
        abort(404)

    transitions = jc.get('api/latest/issue/{key}/transitions'.format(key=key))
    show_resolve = False
    for k, t in transitions.items():
        if t['name'] == "Resolve Issue":
            show_resolve = True
            break

    return render_template('ticketview.html', user=user, issue=issue,
            show_resolve=show_resolve)


@app.route('/issue/<string:key>/resolve', methods=['POST'])
def resolve_issue(key):
    user = jc.get('auth/latest/session')
    if 'status-code' in user and user['status-code'] == 401:
        abort(401)

    try:
        issue = jc.issue(key)
    except (KeyError, ValueError):
        abort(404)

    transitions = jc.get('api/latest/issue/{key}/transitions'.format(key=key))
    transid = 0
    for k, t in transitions.items():
        if t['name'] == "Resolve Issue":
            transid = k
            break

    if transid <= 0:
        abort(403)

    data = {
        'transition': transid,
        'fields': {},
    }

    if 'comment' in request.form:
        data['comment'] = request.form['comment']
    jc.post('api/latest/issue/{key}/transitions'.format(key=key), data)

    return redirect(url_for('issue', key=key))


@app.route('/issue/new', methods=['GET', 'POST'])
def newissue():
    # XXX: the JIRA 4.3 REST API does not support creating issues
    abort(404)

    user = jc.get('auth/latest/session')
    if 'status-code' in user and user['status-code'] == 401:
        abort(401)

    if request.method == 'POST':
        newissue = jc.post('api/latest/issue', {
            'fields': {
                'summary': request.form['summary'],
                'description': request.form['description'],
            },
        })

    return render_template('newticket.html', user=user)


@app.route('/projects')
def projects():
    user = jc.get('auth/latest/session')
    if 'status-code' in user and user['status-code'] == 401:
        abort(401)

    projects = jc.get('api/latest/project')
    return render_template('projects.html', user=user, projects=projects)


@app.route('/project/<string:key>')
@app.route('/project/<string:key>/<int:start>')
def project(key, start=0):
    user = jc.get('auth/latest/session')
    if 'status-code' in user and user['status-code'] == 401:
        abort(401)

    project = jc.get('api/latest/project/{key}'.format(key=key))
    if 'errorMessages' in project:
        abort(404)

    result = jc.post('api/latest/search', {
        'jql': 'project = "{key}"'.format(key=key),
        'startAt': start,
        'maxResults': app.config['ISSUES_PER_PAGE'],
    })
    if u'status-code' in result:
        abort(result[u'status-code'])

    issues = []
    if 'issues' in result:
        for item in result['issues']:
            issue = jc.issue(item['key'])
            issues.append(issue)

    # pagination
    if start > 0:
        start_prev = start - app.config['ISSUES_PER_PAGE']
        if start_prev < 0:
            start_prev = 0
    else:
        start_prev = -1
    if start + app.config['ISSUES_PER_PAGE'] < result['total']:
        start_next = start + app.config['ISSUES_PER_PAGE']
    else:
        start_next = -1

    return render_template('project.html', user=user, project=project,
            issues=issues, start_prev=start_prev, start_next=start_next)


@app.route('/search', methods=['GET', 'POST'])
def search():
    user = jc.get('auth/latest/session')
    if 'status-code' in user and user['status-code'] == 401:
        abort(401)

    if request.method == 'POST':
        return search_results(request.form['q'])

    return render_template('search.html', user=user)


def search_results(query, start=0):
    user = jc.get('auth/latest/session')
    if 'status-code' in user and user['status-code'] == 401:
        abort(401)

    result = jc.post('api/latest/search', {
        'jql': 'summary ~ "{query}" OR description ~ "{query}"'.format(query=query),
        'startAt': start,
        'maxResults': app.config['ISSUES_PER_PAGE'],
    })
    if u'status-code' in result:
        abort(result[u'status-code'])

    issues = []
    if 'issues' in result:
        for item in result['issues']:
            issue = jc.issue(item['key'])
            issues.append(issue)

    return render_template('results.html', user=user, issues=issues)


@app.route('/contact')
def contact():
    user = jc.get('auth/latest/session')
    return render_template('contact.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = jc.get('auth/latest/session')
    if 'name' in user:
        return redirect(url_for('index'))

    error = ""

    if request.method == 'POST':
        result = jc.post('auth/latest/session', {
            'username': request.form['username'],
            'password': request.form['password'],
        })
        if 'session' in result:
            session['JSESSIONID'] = result['session']['value']
            return redirect(url_for('index'))
        else:
            error = result['errorMessages'][0]

    return render_template('login.html', user={}, error=error)


@app.route('/login/<string:session_id>')
def login_sessid(session_id):
    session['JSESSIONID'] = session_id
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    jc.delete('auth/latest/session')
    if 'JSESSIOID' in session:
        session.pop('JSESSIONID', none)
    return render_template('logout.html', user={})


@app.errorhandler(401)
def error401(error):
    return redirect(url_for('login'))
