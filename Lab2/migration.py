from google.cloud import datastore

DS = datastore.Client()


def add_event(event, parent_id):
    """Adding the event to the database.

    :return: The unique ID of the new event.
    :param event:The event need to be added to the database.
    """
    entity = datastore.Entity(key=DS.key('Lab2-event', parent=DS.key('Lab2-user', parent_id)))
    entity.update({
        'name': event['name'],
        'date': event['date']
    })

    DS.put(entity)
    return entity.id


def _del_event(ID):
    """Delete an event according to its unique ID.

    :param ID:The unique id of target event
    """
    key = DS.key('Lab2-event', int(ID))
    DS.delete(key)


def get_all():
    """Getting all events stored in the old database.

    :return events: All events stored in the database.
    """
    query = DS.query(kind='Lab1-event')

    events = query.fetch()
    result = []
    for event in events:
        temp = dict(event)
        temp['ID'] = event.id
        result.append(temp)
    return result


def get_parent():
    query = DS.query(kind='Lab2-user')
    events = query.fetch()
    for event in events:
        return event.id


if __name__ == '__main__':
    parent_id = get_parent()
    events = get_all()
    for event in events:
        add_event(event, parent_id)
    # for event in events:
    #     _del_event(event['ID'])
