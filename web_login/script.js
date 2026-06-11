document.getElementById("loginForm").addEventListener("submit", function(e){

    e.preventDefault();

    let username = document.getElementById("username").value.trim();
    let password = document.getElementById("password").value.trim();
    let message = document.getElementById("message");

    if(username === "" || password === ""){
        message.style.color = "red";
        message.textContent = "All fields are required!";
        return;
    }

    if(username === "admin" && password === "12345"){
        message.style.color = "green";
        message.textContent = "Login Successful!";
    }
    else{
        message.style.color = "red";
        message.textContent = "Invalid Username or Password!";
    }
});
