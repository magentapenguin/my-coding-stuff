const table = document.getElementById("url-list");

fetch("/api/urls")
    .then((response) => response.json())
    .then((data) => {
        Object.entries(data).forEach((url) => {
            console.log(url);
            const row = document.createElement("tr");
            const shortUrl = document.createElement("td");
            const originalUrl = document.createElement("td");

            const link = document.createElement("a");
            link.href = '/'+url[0];
            link.textContent = '/'+url[0];
            shortUrl.appendChild(link);
            
            originalUrl.textContent = url[1];

            row.appendChild(shortUrl);
            row.appendChild(originalUrl);
            table.appendChild(row);
        });
    })
    .catch((error) => console.error(error));