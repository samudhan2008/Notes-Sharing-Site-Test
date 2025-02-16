document.addEventListener("DOMContentLoaded", function () {
    const body = document.body;

    if (localStorage.getItem("theme") === "dark") {
        body.classList.add("dark-mode");
    }
});
