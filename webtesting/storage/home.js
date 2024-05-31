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


document.getElementById("delete").addEventListener("click", function() {
    document.getElementById("delete-account").showModal();
});

document.getElementById("upload-file").addEventListener("click", function() {
    document.getElementById("file-modal").showModal();
})

document.getElementById("file").style.opacity = 0;
document.getElementById("file").style.position = "absolute";
document.getElementById("file").style.left = "-9999px";

function updatefiles() {
    const files = document.getElementById("file").files;
    
    document.getElementById("upload-file-list").innerHTML = "";
    if (files.length > 0) {
        Object.values(files).forEach(file => {
            var fileRow = document.createElement("tr");
            fileRow.innerHTML = `<td>${file.name}</td><td>${fmtsize(file.size)}</td><td>${file.type}</td>`
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
        fetch("/storage/storage?file="+element.dataset.name, {
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