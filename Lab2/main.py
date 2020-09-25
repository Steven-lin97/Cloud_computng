import json
import random
import string
from datetime import datetime, timedelta
from flask import *
from google.cloud import datastore
# import libs.bcrypt as bcrypt
import bcrypt
import pytz

app = Flask(__name__)
DS = datastore.Client()
length = 10
# salt = b'$2b$10$1z3/gAC13A9.6aC0sRIqM.'
salt = bcrypt.gensalt(10)


def get_random_string(length):
    """Generate a random string of specific length.

    @param length: The length of string.
    @return: A random string with only character.
    """
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def _add_event(event, parent_id):
    """Adding the event to the database.

    @param event: The event need to be added to the database.
    @param parent_id: The id of current user.
    @return: The unique ID of the new event.
    """
    entity = datastore.Entity(key=DS.key('Lab2-event', parent=DS.key('Lab2-user', parent_id)))
    entity.update({
        'name': event['name'],
        'date': event['date']
    })
    DS.put(entity)
    return entity.id


def _del_event(ID, parent_ID):
    """Delete an event according to its unique ID.

    @param ID: The unique id of target event
    @param parent_ID: The id of current user.
    """
    key = DS.key('Lab2-user', int(parent_ID), 'Lab2-event', int(ID))
    DS.delete(key)


def get_all(parent_id):
    """Getting all events stored in the database.
    Automatically delete past events.

    :return events: All events stored in the database.
    @param parent_id: The id of current user.
    """
    ancestor = DS.key('Lab2-user', parent_id)
    query = DS.query(kind='Lab2-event', ancestor=ancestor)

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
    query = DS.query(kind='Lab2-session')
    query.add_filter('token', '=', token)

    events = query.fetch()
    for event in events:
        if event['expire'] < pytz.utc.localize(datetime.now()):
            _del_session(token)
        return event.key.parent.id
    return False


def _del_session(token):
    """Delete a session from database.

    @param token: The token of session.
    """
    query = DS.query(kind='Lab2-session')
    query.add_filter('token', '=', token)

    events = query.fetch()
    keys = []
    for event in events:
        keys.append(event.key)

    for key in keys:
        DS.delete(key)


def _create_session(parent_id):
    """Create a session token and store it.

    @param parent_id: The session owner's ID.
    @return: The token generated.
    """
    entity = datastore.Entity(key=DS.key('Lab2-session', parent=DS.key('Lab2-user', parent_id)))
    entity.update({
        'token': get_random_string(length),
        'expire': datetime.now() + timedelta(hours=9)
    })
    DS.put(entity)
    return entity['token']


def _verify_user(uname, passwd):
    """Check if the user name and password matches.

    @param uname: User name.
    @param passwd: Password.
    @return: The id of the user if matches.
    """
    query = DS.query(kind='Lab2-user')
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
    query = DS.query(kind='Lab2-user')
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
    entity = datastore.Entity(key=DS.key('Lab2-user'))
    entity.update({
        'uname': uname,
        'passwd': passwd
    })
    DS.put(entity)
    return entity.id


@app.route('/')
def root():
    """Generate the web page.

    :return: Render template of web page.
    """
    token = request.cookies.get('token')
    if not token:
        res = redirect('/login', code=401)
    else:
        if _search_session(token):
            res = make_response(render_template('index.html'))
        else:
            res = redirect('/login', code=401)

    return res


@app.route('/login', methods=['POST', 'GET'])
def login_page():
    """User login. Create a session if the username and password are correct.

    @return: Redirect address.
    """
    if request.method == 'GET':
        res = make_response(render_template('login.html'))
    if request.method == 'POST':
        data = json.loads(request.data)
        if not data['uname']:
            abort(make_response('User name cannot be empty!', 400))
        if not data['passwd']:
            abort(make_response('Password cannot be empty!', 400))
        uname = data['uname']
        passwd = bcrypt.hashpw(data['passwd'].encode('utf-8'), salt)
        user_id = _verify_user(uname, passwd)
        if user_id:
            token = _create_session(user_id)
            res = make_response('/')
            res.set_cookie('token', token)
        else:
            abort(make_response('User name or Password is not correct!', 400))
    return res


@app.route('/signup', methods=['POST'])
def sign_up():
    """Add a new user into database, create a session and then redirect to the main page.

    @return: Redirect address.
    """
    data = json.loads(request.data)
    if not data['uname']:
        abort(make_response('User name cannot be empty!', 400))
    if not data['passwd']:
        abort(make_response('Password cannot be empty!', 400))
    uname = data['uname']
    passwd = bcrypt.hashpw(data['passwd'].encode('utf-8'), salt)
    user_id = _add_user(uname, passwd)
    if user_id:
        token = _create_session(user_id)
        res = make_response('/')
        res.set_cookie('token', token)
    else:
        abort(make_response('User is already exist!', 400))
    return res


@app.route('/events')
def send_events():
    """Select all events in database.
    Send them to the client.

    :return: All entities in database in json form.
    """
    token = request.cookies.get('token')
    parent_id = _search_session(token)
    if not parent_id:
        abort(make_response('Session expired.', 401))
    else:
        events = events2json(get_all(parent_id))
    return events


@app.route('/event', methods=['POST'])
def add_event():
    """Insert the event into database.
    If the event doesn't have year, insert the next occurrence of a matching date.

    :return: Status Information.
    """
    token = request.cookies.get('token')
    parent_id = _search_session(token)
    if not parent_id:
        abort(make_response('Session expired.', 401))
    else:
        event = json.loads(request.data)
        if not event['name']:
            abort(make_response('Name cannot be empty!', 400))
        if not event['date']:
            abort(make_response('Date cannot be empty!', 400))
        date = event['date'].split('/')
        for i in range(len(date)):
            try:
                date[i] = int(date[i])
            except ValueError:
                abort(make_response('Date format is wrong!', 400))

        if len(date) != 2 and len(date) != 3:
            abort(make_response('Date format is wrong!', 400))
        if len(date) == 3:
            event['date'] = datetime(date[0], date[1], date[2])
        if len(date) == 2:
            temp = datetime(2020, date[0], date[1])
            event['date'] = temp if temp > datetime.now() else datetime(2021, date[0], date[1])

        token = request.cookies.get('token')
        parent_id = _search_session(token)
        if not parent_id:
            abort(make_response('Session expired.', 401))
        else:
            new_ID = _add_event(event, parent_id)

        return json.dumps({'text': 'Success! The unique ID of the new event is ' + str(new_ID)})


@app.route('/event/<event_id>', methods=['DELETE'])
def del_event(event_id):
    """Delete an event according to the unique ID generated by datastore.

    :param event_id: The unique ID of target event.
    :return: Status Information.
    """
    token = request.cookies.get('token')
    parent_id = _search_session(token)
    if not parent_id:
        return make_response('Session expired.', 401)
    else:
        _del_event(event_id, parent_id)

    return json.dumps({'text': 'Success! Target event has been deleted!'})


@app.route('/logout', methods=['DELETE'])
def logout():
    """Delete the session in database and log out.

    @return: Redirect address.
    """
    token = request.cookies.get('token')
    _del_session(token)
    return json.dumps({'text': '/login'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
