document.addEventListener("DOMContentLoaded", () => {
    const passwordInput = document.getElementById("password");
    const requirementText = document.getElementById("password-requirement");

    passwordInput.addEventListener("input", () => {
        if (passwordInput.value.length >= 8) {
            requirementText.classList.remove("text-red");
            requirementText.classList.add("text-green");
            requirementText.textContent = "Must be at least 8 characters long.";
        } else {
            requirementText.classList.remove("text-green");
            requirementText.classList.add("text-red");
            requirementText.textContent = "Must be at least 8 characters long.";
        }
    });
});
