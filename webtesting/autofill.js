import dompurify from 'https://cdn.jsdelivr.net/npm/dompurify/+esm'

function getFromQuery(x) {
    const url = new URL(window.location.href)
    return url.searchParams.get(x)
}


export function autofill() {
    document.querySelectorAll('input, select, textarea').forEach((input) => {
        console.log('Checking', input.name, 'with', getFromQuery(input.name))
        if (input.name && getFromQuery(input.name) && input.type !== 'hidden' && input.type !== 'submit' && input.type !== 'button' && input.type !== 'file') {
            if (input.type === 'radio' || input.type === 'checkbox') {
                if (input.value === getFromQuery(input.name)) {
                    input.checked = true
                }
            } else if (input.tagName === 'SELECT') {
                input.value = dompurify.sanitize(getFromQuery(input.name))
            } else {
                input.value = dompurify.sanitize(getFromQuery(input.name)) // Sanitize to prevent XSS
            }
            input.classList.add('autofilled')
            input.autofillcallback = input.addEventListener('input', (e) => {
                input.classList.remove('autofilled')
                if (input.type === 'radio' || input.type === 'checkbox') {
                    document.querySelectorAll(`input[name="${input.name}"]`).forEach((i) => {
                        i.classList.remove('autofilled')
                        i.removeEventListener('input', i.autofillcallback)
                    })
                }
                input.removeEventListener('input', input.autofillcallback)
            })
        }
        
    })
}

window.runAutoFill = autofill