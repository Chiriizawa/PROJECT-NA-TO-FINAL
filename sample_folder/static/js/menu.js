// Load cart from localStorage or initialize empty object
const cart = JSON.parse(localStorage.getItem('cart')) || {};

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
        cart[name].quantity += 1; // Increase quantity with no limit
    } else {
        cart[name] = { price, quantity: 1 };
    }

    localStorage.setItem('cart', JSON.stringify(cart)); // Save to localStorage
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
    localStorage.setItem('cart', JSON.stringify(cart));
    renderCart();
}

// Function to update quantity when typed manually
function updateQuantity(name, newQuantity) {
    let quantity = parseInt(newQuantity);
    if (quantity > 0) {
        cart[name].quantity = quantity; // No limit on quantity
    } else {
        delete cart[name]; // Remove item if quantity is 0 or invalid
    }
    localStorage.setItem('cart', JSON.stringify(cart));
    renderCart();
}

// Function to render cart (without images)
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
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="delete cart['${name}']; renderCart();">×</button>
                </div>
            </div>`;
    }

    document.getElementById("total-amount").textContent = `₱${subTotal}.00`;
}

// Function to update checkout form with cart data
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

// Ensure cart data is updated before submitting
document.getElementById("checkout-form").addEventListener("submit", function () {
    updateCartForm();
});

// Load cart on page load
document.addEventListener("DOMContentLoaded", function () {
    renderCart();
});
