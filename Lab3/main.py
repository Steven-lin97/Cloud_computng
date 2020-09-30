import base64
import hashlib
import json
import os
from datetime import datetime

import requests
from flask import *
from google.cloud import datastore

app = Flask(__name__)
DS = datastore.Client()
oidc_state = ''


def get_client_credential():
    """Get OAuth credential.

    Returns:Client ID and Client secret of credential.

    """
    ID = DS.get(DS.key('secret', 'oidc'))['client_ID']
    secret = DS.get(DS.key('secret', 'oidc'))['client_secret']
    return {'ID': ID, 'secret': secret}


def get_all(parent_id):
    """Getting all events stored in the database.
    Automatically delete past events.

    :return events: All events stored in the database.
    @param parent_id: The id of current user.
    """
    ancestor = DS.key('Lab3-user', parent_id)
    query = DS.query(kind='Lab3-event', ancestor=ancestor)

    events = query.fetch()
    result = []
    for event in events:
        temp = dict(event)
        if temp['date'].timestamp() < datetime.now().timestamp():
            DS.delete(event.key)
            continue
        temp['ID'] = event.id
        result.append(temp)
    return result


def events2json(events):
    """Transfer event objects into JSON format.
    Generate string of date and ETA from the date property.
    Sort events by the ETA.

    :param events: Event objects need to be transfer.
    :return: Json format events.
    """
    events.sort(key=lambda event: event['date'])

    for event in events:
        timestamp = datetime.timestamp(event['date'])
        current = datetime.now().timestamp()
        event['date'] = event['date'].strftime("%m/%d/%Y")
        event['ETA'] = ''
        diff = int(timestamp - current)
        if diff < 86400:
            event['ETA'] = ':' + str(diff % 60) + ' left.'
            diff = diff // 60
            event['ETA'] = ':' + str(diff % 60) + event['ETA']
            diff = diff // 60
            event['ETA'] = str(diff) + event['ETA']
        else:
            event['ETA'] = str(diff // 86400) + ' days later.'
    return json.dumps(events)


def _search_session(token):
    """Verify a session. Delete the session if it is expired.

    @param token: Session token.
    @return: The id of session owner if the session is still active.
    """
    query = DS.query(kind='Lab3-session')
    query.add_filter('token', '=', token)

    events = query.fetch()
    for event in events:
        return event.key.parent.id
    return False


def _del_session(token):
    """Delete a session from database.

    @param token: The token of session.
    """
    query = DS.query(kind='Lab3-session')
    query.add_filter('token', '=', token)

    events = query.fetch()
    keys = []
    for event in events:
        keys.append(event.key)

    for key in keys:
        DS.delete(key)


def _create_session(parent_id, token):
    """Create a session token and store it.

    @param parent_id: The session owner's ID.
    @return: The token generated.
    """
    entity = datastore.Entity(key=DS.key('Lab3-session', parent=DS.key('Lab3-user', parent_id)))
    entity.update({
        'token': token,
        'expire': datetime.now()
    })
    DS.put(entity)
    return entity['token']


def _verify_user(uname, passwd):
    """Check if the user name and password matches.

    @param uname: User name.
    @param passwd: Password.
    @return: The id of the user if matches.
    """
    query = DS.query(kind='Lab3-user')
    query.add_filter('uname', '=', uname)
    query.add_filter('passwd', '=', passwd)

    events = query.fetch()
    for event in events:
        return event.id
    return None


def _search_user(uname):
    """ Search the given user.

    @param uname: User name.
    @return: If the user is exist.
    """
    query = DS.query(kind='Lab3-user')
    query.add_filter('uname', '=', uname)
    events = query.fetch()
    for event in events:
        return True
    return False


def _add_user(uname, passwd):
    """ Add a user to database.

    @param uname: User name.
    @param passwd: Password.
    @return: The id of new user.
    """
    if _search_user(uname):
        return None
    entity = datastore.Entity(key=DS.key('Lab3-user'))
    entity.update({
        'uname': uname,
        'passwd': passwd
    })
    DS.put(entity)
    return entity.id


@app.route('/')
def root():
    """Redirect user to login page or main page.
    Check for session token to decide which url should be redirected to.

    :return: Redirect response.
    """
    token = request.cookies.get('state')
    if not token or not _search_session(token):
        res = redirect('/login', code=401)
    else:
        res = redirect('/oidauth')
    return res


@app.route('/login')
def login_page():
    """User login. Create a session if the username and password are correct.

    @return: Redirect address.
    """
    return make_response(render_template('login.html'))


@app.route('/login_google')
def google_login():
    client_credential = get_client_credential()
    global oidc_state
    oidc_state = hashlib.sha256(os.urandom(1024)).hexdigest()
    # res = redirect('https://accounts.google.com/o/oauth2/v2/auth?'
    #                'response_type=code&'
    #                'client_id=' + client_credential['ID'] +
    #                '&scope=openid%20email&'
    #                'redirect_uri=https%3A//lab3-291100.ue.r.appspot.com/oidauth&'
    #                'state=' + token +
    #                '&nonce=1234', code=302)
    # return res

    return 'https://accounts.google.com/o/oauth2/v2/auth?' \
           'response_type=code&' \
           'client_id=' + client_credential['ID'] + \
           '&scope=openid%20email&' \
           'redirect_uri=https://lab3-291100.ue.r.appspot.com/oidauth&' \
           'state=' + oidc_state + \
           '&nonce=1234'


@app.route('/oidauth')
def main_page():
    code = request.args['code']
    state = request.args['state']
    if state != oidc_state:
        abort(make_response('Credential not valid!', 401))
    cred = get_client_credential()
    para = {
        'code': code,
        'client_id': cred['ID'],
        'client_secret': cred['secret'],
        'redirect_uri': 'https://lab3-291100.ue.r.appspot.com/oidauth',
        'grant_type': 'authorization_code'
    }
    token_res = requests.post('https://www.googleapis.com/oauth2/v4/token', para).json()
    token = token_res['access_token']
    id_token = token_res['id_token']
    _, body, _ = id_token.split('.')
    body += '=' * (-len(body) % 4)
    claims = json.loads(base64.urlsafe_b64decode(body.encode('utf-8')))
    sub = claims['sub']
    email = claims['email']
    user_id = _verify_user(sub, email)
    if not user_id:
        user_id = _add_user(sub, email)
    _create_session(user_id, token)
    res = make_response(render_template('index.html'))
    res.set_cookie('state', token)
    return res


@app.route('/events')
def send_events():
    """Select all events in database.
    Send them to the client.

    :return: All entities in database in json form.
    """
    token = request.cookies.get('state')
    parent_id = _search_session(token)
    if not parent_id:
        abort(make_response('Session expired.', 401))
    else:
        events = events2json(get_all(parent_id))
    return events


if __name__ == '__main__':
    # jsonurl = requests.get('https://accounts.google.com/.well-known/openid-configuration')
    # Disc_Doc = json.loads(jsonurl.text)
    app.run(host='127.0.0.1', port=8080, debug=True)
