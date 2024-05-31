
function humanizeTimeDate(date) {
    let time = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: 'numeric' });
    let strDate = date.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
    return `${time} ${strDate}`;
}


new Chart(
    document.getElementById('visits'),
    {
        type: 'line',
        data: {
            labels: data.map(row => humanizeTimeDate(row.year)),
            datasets: [
                {
                    label: 'Acquisitions by year',
                    data: data.map(row => row.count),
                    fill: 'origin',
                }
            ]
        }
    }
);



var darkmode = window.matchMedia('(prefers-color-scheme: dark)');
darkmode.addEventListener('change', function() {
    Chart.defaults.color = getComputedStyle(document.getElementById('visits')).getPropertyValue('--text-color');
});
Chart.defaults.color = getComputedStyle(document.getElementById('visits')).getPropertyValue('--text-color');