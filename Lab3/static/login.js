'use strict';

function reqJSON(method, url, data) {
    return new Promise((resolve, reject) => {
        let xhr = new XMLHttpRequest();
        xhr.open(method, url);
        xhr.setRequestHeader("Content-type", "application/json");
        xhr.setRequestHeader("Access-Control-Allow-Headers", "*");
        xhr.withCredentials = true
        xhr.Ac
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
    reqJSON('GET', '/login_google').then(({status, data}) => {
            window.location.href = data;
        }
    ).catch(({status, data}) => {
        if (status === 302)
            window.location.href = data;
        alert('ERROR: ' + data);
    })
}
