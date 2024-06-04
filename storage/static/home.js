
import { initTooltips } from '/tooltip.js';
initTooltips();

function fmtsize(size) {
    if (size < 1024) {
        return size + "B";
    }
    size /= 1024;
    if (size < 1024) {
        return size.toFixed(2) + "KB";
    }
    size /= 1024;
    if (size < 1024) {
        return size.toFixed(2) + "MB";
    }
    size /= 1024;
    return size.toFixed(2) + "GB";
}

function precheck(len) {
    fetch("/storage?precheck="+len, {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }
    }).then(response => {
        if (response.ok) {
            return response.json().then((x)=>{return x["output"]});
        } else {
            return false;
        }
    })
}

document.getElementById("delete").addEventListener("click", function() {
    document.getElementById("delete-account").showModal();
});

document.getElementById("upload-file").addEventListener("click", function() {
    document.getElementById("file-modal").showModal();
})

document.getElementById("file").style.opacity = 0;
document.getElementById("file").style.position = "absolute";
document.getElementById("file").style.left = "-9999px";

async function updatefiles() {
    const files = document.getElementById("file").files;
    
    document.getElementById("upload-file-list").innerHTML = "";
    if (files.length > 0) {
        Object.values(files).forEach(file => {
            var fileRow = document.createElement("tr");
            if (!precheck(file.size)){
                fileRow.innerHTML = `<td>${file.name}</td><td class="color-accent red-accent"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="fa-svg-man"><!--!Font Awesome Free 6.5.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2024 Fonticons, Inc.--><path d="M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM175 175c9.4-9.4 24.6-9.4 33.9 0l47 47 47-47c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-47 47 47 47c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-47-47-47 47c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l47-47-47-47c-9.4-9.4-9.4-24.6 0-33.9z"/></svg> File too big!</td><td>${file.type}</td>`
            } else {
                fileRow.innerHTML = `<td>${file.name}</td><td>${fmtsize(file.size)}</td><td>${file.type}</td>`
            }
            fileRow.dataset.name = file.name;
            document.getElementById("upload-file-list").appendChild(fileRow);
        });
    } else {
        document.getElementById("upload-file-list").innerHTML = "<tr><td colspan='3'>No file selected</td></tr>";
    }
}


document.getElementById("file").addEventListener("change", updatefiles)

const delbtns = document.getElementsByClassName("del-btn")
Array.from(delbtns).forEach(element => {
    console.log(element);
    element.addEventListener("click", function() {
        fetch("/storage?file="+element.dataset.name, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            }
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            }
        })
    })
});

document.getElementById("upload-cancel").addEventListener("click", function() {
    document.getElementById("file-modal").close();
})