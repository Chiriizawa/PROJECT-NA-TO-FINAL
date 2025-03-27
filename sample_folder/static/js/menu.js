// Load cart from localStorage or initialize empty cart
let cart = loadCartFromLocalStorage() || {};

// Function to load cart from localStorage
function loadCartFromLocalStorage() {
    const cartData = localStorage.getItem("cart");
    return cartData ? JSON.parse(cartData) : {};
}

// Function to save cart to localStorage
function saveCartToLocalStorage() {
    localStorage.setItem("cart", JSON.stringify(cart));
}

// Function to toggle cart visibility
function toggleCart() {
    var cartContent = document.getElementById("cart-content");
    var cartContainer = document.querySelector(".cart-container");

    if (cartContent.style.display === "none") {
        cartContent.style.display = "block"; // Show cart
        cartContainer.style.height = "auto"; // Reset height
    } else {
        cartContent.style.display = "none"; // Hide cart
        cartContainer.style.height = "40px"; // Set minimized height
    }
}

// Function to add items to cart
function addToCart(name, price) {
    if (cart[name]) {
        cart[name].quantity += 1; // Increase quantity
    } else {
        cart[name] = { price, quantity: 1 };
    }

    saveCartToLocalStorage(); // Save updated cart
    renderCart(); // Update cart display
}

// Function to remove items from cart
function removeFromCart(name) {
    if (cart[name]) {
        if (cart[name].quantity > 1) {
            cart[name].quantity -= 1;
        } else {
            delete cart[name];
        }
    }
    saveCartToLocalStorage(); // Save updated cart
    renderCart(); // Update cart display
}

// Function to update quantity when typed manually
function updateQuantity(name, newQuantity) {
    let quantity = parseInt(newQuantity);
    if (quantity > 0) {
        cart[name].quantity = quantity; // Update quantity
    } else {
        delete cart[name]; // Remove item if quantity is 0
    }
    saveCartToLocalStorage(); // Save updated cart
    renderCart(); // Update cart display
}

// Function to clear the entire cart
function clearCart() {
    cart = {}; // Reset cart to empty object
    saveCartToLocalStorage(); // Save empty cart
    renderCart(); // Re-render cart
}

// Function to render cart
function renderCart() {
    const cartItems = document.getElementById("cart-items");
    cartItems.innerHTML = "";
    let subTotal = 0;

    for (const [name, item] of Object.entries(cart)) {
        subTotal += item.price * item.quantity;
        cartItems.innerHTML += `
            <div class="cart-item d-flex justify-content-between align-items-center mb-2">
                <div class="d-flex align-items-center">
                    <span>${name}</span>
                    <small class="ms-2">₱${item.price * item.quantity}.00</small>
                </div>
                <div class="d-flex align-items-center">
                    <button class="btn btn-sm btn-outline-secondary" onclick="removeFromCart('${name}')">-</button>
                    <input type="number" class="form-control text-center mx-1" style="width: 50px;" 
                        value="${item.quantity}" onchange="updateQuantity('${name}', this.value)">
                    <button class="btn btn-sm btn-outline-secondary me-3" onclick="addToCart('${name}', ${item.price})">+</button>
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="deleteItem('${name}')">×</button>
                </div>
            </div>`;
    }

    document.getElementById("total-amount").textContent = `₱${subTotal}.00`;

    if (Object.keys(cart).length === 0) {
        cartItems.innerHTML = `<p class="text-white">Your cart is empty.</p>`;
    }
}

// Function to delete an item from the cart
function deleteItem(name) {
    delete cart[name]; // Remove item
    saveCartToLocalStorage(); // Save updated cart
    renderCart(); // Re-render cart
}

// Function to update hidden inputs before submitting
function updateCartForm() {
    let cartInputs = document.getElementById("cart-inputs");
    cartInputs.innerHTML = "";

    let index = 0;
    for (const [name, item] of Object.entries(cart)) {
        cartInputs.innerHTML += `
            <input type="hidden" name="item_name_${index}" value="${name}">
            <input type="hidden" name="item_price_${index}" value="${item.price}">
            <input type="hidden" name="item_quantity_${index}" value="${item.quantity}">
        `;
        index++;
    }
}

// Clear cart on form submission after checkout
document.getElementById("checkout-form").addEventListener("submit", function () {
    updateCartForm(); // Update hidden inputs
    clearCart(); // Clear cart after successful checkout
    localStorage.removeItem("cart"); // Clear localStorage on checkout
});

// Load and render cart on page load
document.addEventListener("DOMContentLoaded", function () {
    renderCart(); // Render cart with loaded data
});
