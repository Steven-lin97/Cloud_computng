'use strict';

let cookie;
let uname = '';
let passwd = '';

function reqJSON(method, url, data) {
    return new Promise((resolve, reject) => {
        let xhr = new XMLHttpRequest();
        xhr.open(method, url);
        xhr.setRequestHeader("Content-type", "application/json");
        xhr.withCredentials = true
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

function login() {
    uname = document.getElementById('uname').value;
    passwd = document.getElementById('passwd').value;
    reqJSON('POST', '/login', JSON.stringify({uname: uname, passwd: passwd})).then(({status, data}) => {
        window.location.href = data
    })
        .catch(({status, data}) => {
            console.log('reject')
            // if (status === 302)
            //     window.location.href='/'
            // cookie = data
            // Display an error.
            alert('ERROR: ' + data);
        });
}


function signup() {
    uname = document.getElementById('uname').value;
    passwd = document.getElementById('passwd').value;
    reqJSON('POST', '/signup', JSON.stringify({uname: uname, passwd: passwd})).then(({status, data}) => {
        window.location.href = data
    })
        .catch(({status, data}) => {
            console.log(data)
            // if (status === 302)
            //     window.location.href='/'
            // cookie = data
            // Display an error.
            alert('ERROR: ' + data);
        });
}

// document.addEventListener('DOMContentLoaded', getEvents);
