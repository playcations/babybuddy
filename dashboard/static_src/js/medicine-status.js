// Medicine Status Card JavaScript functionality
document.addEventListener("DOMContentLoaded", function () {
  // Handle repeat dose buttons
  document.querySelectorAll(".repeat-dose-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const medicineId = this.dataset.medicineId;
      const medicineName = this.dataset.medicineName;

      // Check if medicine is in safety window
      const medicineItem = this.closest(".medicine-status-item");
      const statusBadge = medicineItem.querySelector(".badge");
      const isInSafetyWindow =
        statusBadge && statusBadge.classList.contains("bg-warning");

      let confirmMessage;
      if (isInSafetyWindow) {
        const statusText = statusBadge.textContent.trim();
        confirmMessage = `⚠️ WARNING: ${medicineName} is still in safety window (${statusText}).\n\nAre you sure you want to give another dose now?`;
      } else {
        confirmMessage = `Repeat dose of ${medicineName}?`;
      }

      if (confirm(confirmMessage)) {
        repeatMedicineDose(medicineId, this);
      }
    });
  });

  // Handle remove medicine buttons
  document.querySelectorAll(".remove-medicine-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const medicineId = this.dataset.medicineId;
      const medicineName = this.dataset.medicineName;

      if (confirm(`Remove ${medicineName} from active list?`)) {
        removeMedicineFromActive(medicineId, this);
      }
    });
  });
});

function repeatMedicineDose(medicineId, buttonElement) {
  const originalText = buttonElement.innerHTML;
  buttonElement.innerHTML = '<i class="icon-spinner icon-spin"></i>';
  buttonElement.disabled = true;

  fetch(`/medicine/${medicineId}/repeat-dose/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        location.reload();
      } else {
        alert("Error: " + data.message);
        buttonElement.innerHTML = originalText;
        buttonElement.disabled = false;
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("An error occurred while repeating the dose.");
      buttonElement.innerHTML = originalText;
      buttonElement.disabled = false;
    });
}

function removeMedicineFromActive(medicineId, buttonElement) {
  const originalText = buttonElement.innerHTML;
  buttonElement.innerHTML = '<i class="icon-spinner icon-spin"></i>';
  buttonElement.disabled = true;

  fetch(`/medicine/${medicineId}/remove-active/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        const medicineItem = buttonElement.closest(".medicine-status-item");
        medicineItem.style.transition = "opacity 0.3s ease";
        medicineItem.style.opacity = "0";
        setTimeout(() => {
          medicineItem.remove();
          if (document.querySelectorAll(".medicine-status-item").length === 0) {
            location.reload();
          }
        }, 300);
      } else {
        alert("Error: " + data.message);
        buttonElement.innerHTML = originalText;
        buttonElement.disabled = false;
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("An error occurred while removing the medicine.");
      buttonElement.innerHTML = originalText;
      buttonElement.disabled = false;
    });
}
