const api = "http://127.0.0.1:5000";

window.onload = () => {
    document.getElementById("searchButton").addEventListener("click", searchButtonOnClick);
    document.getElementById("addProduct").addEventListener("click", productFormOnSubmit);
}

searchButtonOnClick = () => {
    let searchName = document.getElementById("searchName").value;
    fetch(`${api}/search?name=${searchName}`)
        .then(response => {
            return response.text().then(text => {
                console.log("Raw response text:", text);
                return JSON.parse(text);
            });
        })
        .then(data => {
            let tableBody = document.getElementById("searchResults").getElementsByTagName("tbody")[0];
            tableBody.innerHTML = "";

            for (let product of data) {
                let row = tableBody.insertRow();

                let idCell = row.insertCell(0);
                idCell.textContent = product.id;

                let nameCell = row.insertCell(1);
                nameCell.textContent = product.name;

                let yearCell = row.insertCell(2);
                yearCell.textContent = product.production_year;

                let priceCell = row.insertCell(3);
                priceCell.textContent = product.price;

                let colorCell = row.insertCell(4);
                colorCell.textContent = product.color;

                let sizeCell = row.insertCell(5);
                sizeCell.textContent = product.size;
            }
        })
        .catch(error => {
            console.error("Error fetching data:", error);
        });
}

productFormOnSubmit = (event) => {
    event.preventDefault();
    let name = document.getElementById("productName").value;
    let year = document.getElementById("productYear").value;
    let price = document.getElementById("productPrice").value;
    let color = document.getElementById("productColor").value;
    let size = document.getElementById("productSize").value;

    fetch(`${api}/add-product`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            production_year: year,
            price: price,
            color: color,
            size: size
        })
    }).then(response => {
        if (response.ok) {
            // Clear the form data
            document.getElementById("productName").value = "";
            document.getElementById("productYear").value = "";
            document.getElementById("productPrice").value = "";
            document.getElementById("productColor").value = "";
            document.getElementById("productSize").value = "";

            // Display the JavaScript alert with "OK" text
            alert("OK");
        } else {
            alert("Error adding product");
        }
    });
}
