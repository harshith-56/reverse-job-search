document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.querySelector("input[type=radio]#login");
    const signupForm = document.querySelector("input[type=radio]#signup");
    const loginTab = document.querySelector("label.login");
    const signupTab = document.querySelector("label.signup");
    const formInner = document.querySelector(".form-inner");
  
    // Tab switching logic
    if (loginForm && signupForm && formInner) {
      loginTab.addEventListener("click", () => {
        loginForm.checked = true;
        formInner.style.marginLeft = "0%";
      });
  
      signupTab.addEventListener("click", () => {
        signupForm.checked = true;
        formInner.style.marginLeft = "-100%";
      });
    }
  
    // Signup link click triggers signup tab
    const signupLink = document.querySelector("#signup-link");
    if (signupLink) {
      signupLink.addEventListener("click", (e) => {
        e.preventDefault();
        signupTab.click();
      });
    }
  
    // Password visibility toggle using emoji
    const toggleIcons = document.querySelectorAll(".toggle-password");
    toggleIcons.forEach(icon => {
      icon.addEventListener("click", () => {
        const passwordInput = icon.previousElementSibling;
        if (passwordInput.type === "password") {
          passwordInput.type = "text";
          icon.textContent = "🙈"; // show monkey to hide
        } else {
          passwordInput.type = "password";
          icon.textContent = "👁️"; // show eye to reveal
        }
      });
    });
  
    // Flash message auto-dismiss
    const message = document.querySelector(".message");
    if (message) {
      setTimeout(() => {
        message.style.opacity = "0";
        setTimeout(() => message.remove(), 500);
      }, 10000);
    }
  });
  