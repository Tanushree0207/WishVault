/**
 * WishVault – Frontend Interactions
 * Accessible modals, light-dismiss, image error fallbacks, and mobile navigation.
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Mobile Sidebar Navigation Drawer
  const mobileToggle = document.getElementById("mobileMenuBtn");
  const sidebar = document.getElementById("appSidebar");
  const sidebarOverlay = document.getElementById("sidebarOverlay");

  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      if (sidebarOverlay) sidebarOverlay.classList.toggle("active");
    });

    if (sidebarOverlay) {
      sidebarOverlay.addEventListener("click", () => {
        sidebar.classList.remove("open");
        sidebarOverlay.classList.remove("active");
      });
    }
  }

  // 2. Safe Image Error Fallback
  // If an external product image URL fails to load, gracefully display the pastel placeholder
  document.querySelectorAll(".product-image").forEach((img) => {
    img.addEventListener("error", function () {
      this.style.display = "none";
      const fallback = this.parentElement.querySelector(".product-image-fallback");
      if (fallback) {
        fallback.style.display = "flex";
      }
    });
  });

  // 3. Purchase Modal Logic (Native HTML5 <dialog> with Light Dismiss)
  const purchaseDialog = document.getElementById("purchaseModal");
  if (purchaseDialog) {
    // Open modal buttons
    document.querySelectorAll("[data-open-purchase-modal]").forEach((button) => {
      button.addEventListener("click", (e) => {
        e.preventDefault();
        const productId = button.getAttribute("data-product-id");
        const productName = button.getAttribute("data-product-name");
        const productPrice = button.getAttribute("data-product-price");

        const form = document.getElementById("purchaseModalForm");
        const modalProductName = document.getElementById("modalProductName");
        const modalAmountInput = document.getElementById("modalAmountInput");

        if (form) {
          form.action = `/purchases/mark/${productId}`;
        }
        if (modalProductName) {
          modalProductName.textContent = productName;
        }
        if (modalAmountInput && productPrice) {
          modalAmountInput.value = parseFloat(productPrice).toFixed(2);
        }

        purchaseDialog.showModal();
      });
    });

    // Close buttons
    purchaseDialog.querySelectorAll("[data-close-dialog]").forEach((closeBtn) => {
      closeBtn.addEventListener("click", () => {
        purchaseDialog.close();
      });
    });

    // Light-dismiss: close when clicking on the backdrop
    purchaseDialog.addEventListener("click", (event) => {
      const rect = purchaseDialog.getBoundingClientRect();
      const isInDialog = (
        rect.top <= event.clientY &&
        event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX &&
        event.clientX <= rect.left + rect.width
      );
      if (!isInDialog) {
        purchaseDialog.close();
      }
    });
  }

  // 4. Auto-dismiss alerts after 5 seconds
  setTimeout(() => {
    document.querySelectorAll(".alert-dismissible").forEach((alert) => {
      alert.style.transition = "opacity 0.5s ease, transform 0.5s ease";
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-10px)";
      setTimeout(() => alert.remove(), 500);
    });
  }, 5000);
});

/**
 * Utility to retrieve CSRF token for AJAX/Fetch calls.
 */
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}
