'use strict';

let events = [];

let clock = self.setInterval(getEvents, 1000)

function reqJSON(method, url, data) {
    return new Promise((resolve, reject) => {
        let xhr = new XMLHttpRequest();
        xhr.open(method, url);
        xhr.responseType = 'json'
        xhr.setRequestHeader("Content-type", "application/json");
        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve({status: xhr.status, data: xhr.response});
            } else {
                reject({status: xhr.status, data: xhr.response});
            }
        };
        xhr.onerror = () => {
            reject({status: xhr.status, data: xhr.response});
        };
        xhr.send(data);
    });
}

function getEvents() {
    reqJSON('GET', '/events')
        .then(({status, data}) => {
            events = data
            let html = '<table><tr><th>ID</th><th>Name</th><th>Date</th><th>ETA</th></tr>';
            let ID = 1;
            for (let event of data) {
                html += '<tr><th>' + ID + '</th><th>' + event.name + '</th><th>' + event.date + '</th><th>' + event.ETA + '</th></tr>';
                ID = ID + 1;
            }
            html += '</table>'
            document.getElementById('events').innerHTML = html;
        })
        .catch(({status, data}) => {
            if (status === 401)
                window.location = '/login';
            // Display an error.
            document.getElementById('events').innerHTML = 'ERROR: ' + JSON.stringify(data);
        });
}

function add_event() {
    let name = prompt('Please enter the name of the new event:');
    let date = prompt('Please enter the date(UTC) of the new event:', 'YYYY/MM/DD');
    reqJSON('POST', '/event', JSON.stringify({name: name, date: date})).then(({status, data}) => {
        alert(data.text);
    })
        .catch(({status, data}) => {
            if (status === 401)
                window.location = '/login';
            // Display an error.
            alert('ERROR: ' + JSON.stringify(data));
        });
}

function del_event() {
    let ID = prompt('Please enter the ID of target event:');
    let uID = events[parseInt(ID) - 1].ID;
    reqJSON('DELETE', '/event/' + uID).then(({status, data}) => {
        alert(data.text);
    })
        .catch(({status, data}) => {
            if (status === 401)
                window.location = '/login';
            // Display an error.
            alert('ERROR: ' + JSON.stringify(data));
        });
}

function log_out() {
    reqJSON('DELETE', '/logout').then(({status, data}) => {
        window.location.href = data.text
    })
        .catch(({status, data}) => {
            // Display an error.
            alert('ERROR: ' + JSON.stringify(data));
        });
}

// document.addEventListener('DOMContentLoaded', getEvents);
  