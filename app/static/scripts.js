document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript Loaded!");

    // Add a simple fade-in animation to the body
    document.body.style.opacity = 0;
    document.body.style.transition = "opacity 1s";
    document.body.style.opacity = 1;

    // Display an alert when a user uploads a file
    const uploadForm = document.querySelector("form[action*='upload_file']");
    if (uploadForm) {
        uploadForm.addEventListener("submit", function () {
            alert("Uploading your PDF...");
        });
    }
});
