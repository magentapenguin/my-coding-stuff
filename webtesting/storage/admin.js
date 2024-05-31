
function humanizeTimeDate(date) {
    let time = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: 'numeric' });
    let strDate = date.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
    return `${time} ${strDate}`;
}


const chart = new Chart(
    document.getElementById('visits'),
    {
        type: 'line',
        data: {
            labels: visits.map(row => humanizeTimeDate(new Date(row.time))),
            datasets: [
                {
                    label: 'Visits',
                    data: visits.map(row => row.visits),
                },
                {
                    label: 'New Visits',
                    data: visits.map(row => row.unique),
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Visits'
                    }
                }
            }
        }
    }
);



var darkmode = window.matchMedia('(prefers-color-scheme: dark)');
darkmode.addEventListener('change', function() {
    chart.color = darkmode.matches ? '#ddd' : '#333';
    chart.update();
});
chart.color = darkmode.matches ? '#ddd' : '#333';
chart.update();

document.getElementById("add-fake-user").addEventListener("click", function() {
    document.getElementById("register-dialog").showModal();
});


async function register(username) {
    console.log(username)
    let response = await fetch('/storage/auth', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({username: username, fake: true})
    })
    if (response.status === 200) {
        return true
    } else {
        throw new Error('Failed to fetch')
    }
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

    if (usernameElement.checkValidity()) {
        console.log('Registering', usernameElement.value)
        register(usernameElement.value).then(output => {
            console.log(output)
            e.target.querySelectorAll('[type="submit"], [type="reset"]').forEach(x=>x.disabled=false)
            e.target.querySelector('[type="submit"]').innerHTML = 'Register'
            document.getElementById('register-dialog').close()
            location.reload()
        }).catch((error) => {
            e.target.querySelectorAll('[type="submit"], [type="reset"]').forEach(x=>x.disabled=false)
            e.target.querySelector('[type="submit"]').innerHTML = 'Register'
        }) 
    } else {
        usernameElement.reportValidity()
        e.target.querySelectorAll('[type="submit"], [type="reset"]').forEach(x=>x.disabled=false)
        e.target.querySelector('[type="submit"]').innerHTML = 'Register'
    }       
}

document.getElementById('register-form').addEventListener('submit', onRegisterSubmit)