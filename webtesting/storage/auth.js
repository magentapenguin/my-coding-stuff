import { client } from '/webtesting/storage/webauthn/index.js';
import { Notyf } from 'https://cdn.jsdelivr.net/npm/notyf@3.10.0/+esm'

const notyf = new Notyf({
    duration: 60000,
    position: {
        x: 'right',
        y: 'bottom',
    },
    dismissible: true,
})

/**
 * Checks if a username is available.
 *
 * @param {string} x - The username to check.
 * @returns {Promise<boolean>} - A promise that resolves to a boolean indicating if the username is available.
 * @throws {Error} - If there was an error fetching the username availability.
 */
async function canihaveusername(x) {
    try {
        let response = await fetch('/storage/canihave/user/'+x, {
            method: 'GET'
        })
        console.log(response)
        if (response.status === 200) {
            let r = await response.json()
            return r['output']
        } else {
            throw new Error('Failed to fetch')
        }
    } catch (error) {
        notyf.error('Failed to check username: '+error.message)
        return false
    }
}

async function getchallenge() {
    // Please note that this is SHOULD NOT fail silently
    let response = await fetch('/storage/auth/', {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
        },
    })
    if (response.status === 200) {
        let x = await response.json()
        console.log(x)
        return x['challenge']
    } else {
        throw new Error('Failed to fetch')
    }
}

async function register(username) {
    console.log(username)
    let challenge = await getchallenge()
    let registration = await client.register(username, challenge, {
        authenticatorType: "both",
        userVerification: "required",
        discoverable: "preferred",
        timeout: 60000,
        attestation: false,
        debug: false,
        domain: location.hostname,
        rp_name: 'bookish-system',
    })
    console.log(registration)
    let response = await fetch('/storage/auth', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(registration)
    })
    if (response.status === 200) {
        return registration
    } else {
        throw new Error('Failed to fetch')
    }
}

async function authenticate() {
    let challenge = await getchallenge()
    let assertion = await client.authenticate([],challenge)
    let response = await fetch('/storage/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(assertion)
    })
    if (response.status === 200) {
        return assertion
    } else {
        throw new Error(response.statusText)
    }
}

function onLoginSubmit(e) {
    let btntext = e.target.innerHTML
    e.target.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="fa-svg-man spin"><path d="M224 32c0-17.7 14.3-32 32-32C397.4 0 512 114.6 512 256c0 46.6-12.5 90.4-34.3 128c-8.8 15.3-28.4 20.5-43.7 11.7s-20.5-28.4-11.7-43.7c16.3-28.2 25.7-61 25.7-96c0-106-86-192-192-192c-17.7 0-32-14.3-32-32z"/></svg> Authenticating...'
    e.target.disabled=true
    e.preventDefault()
    authenticate().then(output => {
        console.log(output)
        window.location.reload()
    }).catch((error) => {
        notyf.error('Failed to authenticate: '+error.message)
        e.target.innerHTML = btntext
        e.target.disabled=false
    })
}

function onRegisterSubmit(e) {
    e.preventDefault()
    let usernameElement = document.getElementById('register-username')
    e.target.querySelector('[type="submit"]').innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="fa-svg-man spin"><path d="M224 32c0-17.7 14.3-32 32-32C397.4 0 512 114.6 512 256c0 46.6-12.5 90.4-34.3 128c-8.8 15.3-28.4 20.5-43.7 11.7s-20.5-28.4-11.7-43.7c16.3-28.2 25.7-61 25.7-96c0-106-86-192-192-192c-17.7 0-32-14.3-32-32z"/></svg> Registering...'
    e.target.querySelectorAll('[type="submit"], [type="reset"]').forEach(x=>x.disabled=true)
    if (usernameElement.value.length < 3) {
        usernameElement.setCustomValidity('Username must be at least 3 characters long')
        usernameElement.reportValidity()
        e.target.querySelectorAll('[type="submit"], [type="reset"]').forEach(x=>x.disabled=false)
        e.target.querySelector('[type="submit"]').innerHTML = 'Register'
        return
    }
    canihaveusername(usernameElement.value).then(output => {
        if (!output) {
            usernameElement.setCustomValidity('Username is already taken')
            usernameElement.reportValidity()
        } else {
            usernameElement.setCustomValidity('')
        }

    if (usernameElement.checkValidity()) {
        console.log('Registering', usernameElement.value)
        register(usernameElement.value).then(output => {
            console.log(output)
            e.target.querySelectorAll('[type="submit"], [type="reset"]').forEach(x=>x.disabled=false)
            e.target.querySelector('[type="submit"]').innerHTML = 'Register'
            document.getElementById('register-dialog').close()
            document.getElementById('success').showModal()
        }).catch((error) => {
            e.target.querySelectorAll('[type="submit"], [type="reset"]').forEach(x=>x.disabled=false)
            e.target.querySelector('[type="submit"]').innerHTML = 'Register'
            notyf.error('Failed to register: '+error.message)
        }) 
    } else {
        usernameElement.reportValidity()
        e.target.querySelectorAll('[type="submit"], [type="reset"]').forEach(x=>x.disabled=false)
        e.target.querySelector('[type="submit"]').innerHTML = 'Register'
    }
    })
       
}

document.getElementById('register-form').addEventListener('submit', onRegisterSubmit)

document.getElementById('register').addEventListener('click', (e) => {
    document.getElementById('register-dialog').showModal()
})

document.getElementById('register-dialog').addEventListener('close', (e) => {
    /*document.getElementById('register-username').value = ''
    document.getElementById('register-username').setCustomValidity('')*/
})

document.getElementById('register-username').addEventListener('change', (e) => {
    canihaveusername(e.target.value).then(output => {
        if (!output) {
            e.target.setCustomValidity('Username is already taken')
            return
        } else {
            e.target.setCustomValidity('')
        }
    })
})

document.querySelector('#register-dialog [type="reset"]').addEventListener('click', (e) => {
    document.getElementById('register-dialog').close()
})

document.getElementById('login').addEventListener('click', onLoginSubmit)
document.getElementById('success-ok').addEventListener('click', onLoginSubmit)

if (!client.isAvailable()) {
    // Just incase the browser doesn't support webauthn
    document.getElementById('login').classList.add('go-away')
    document.getElementById('register').classList.add('go-away')
    document.getElementById('no-support').classList.remove('go-away')
}