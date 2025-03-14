const cart = {};

function addToCart(name, price) {
    if (cart[name]) {
        cart[name].quantity += 1;
    } else {
        cart[name] = { price, quantity: 1 };
    }
    renderCart();
}

function removeFromCart(name) {
    if (cart[name]) {
        if (cart[name].quantity > 1) {
            cart[name].quantity -= 1;
        } else {
            delete cart[name];
        }
    }
    renderCart();
}

function renderCart() {
    const cartItems = document.getElementById("cart-items");
    cartItems.innerHTML = "";
    let subTotal = 0;

    for (const [name, item] of Object.entries(cart)) {
        subTotal += item.price * item.quantity;
        cartItems.innerHTML += `
            <div class="cart-item d-flex justify-content-between align-items-center mb-2">
                <div>
                    <span>${name}</span>
                    <small>₱${item.price * item.quantity}.00</small>
                </div>
                <div class="d-flex align-items-center">
                    <button class="btn btn-sm btn-outline-secondary" onclick="removeFromCart('${name}')">-</button>
                    <input type="text" class="form-control text-center mx-1" style="width: 50px;" value="${item.quantity}" readonly>
                    <button class="btn btn-sm btn-outline-secondary me-3" onclick="addToCart('${name}', ${item.price})">+</button>
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="delete cart['${name}']; renderCart();">×</button>
                </div>
            </div>`;
    }

    document.getElementById("total-amount").textContent = `₱${subTotal}.00`;
}



function updateCartForm() {
    let cartInputs = document.getElementById("cart-inputs");
    cartInputs.innerHTML = "";  // Clear previous inputs

    // Loop through each item in the cart and create hidden input fields
    for (let i = 0; i < cart.length; i++) {
        let item = cart[i];
        cartInputs.innerHTML += `
            <input type="hidden" name="item_name_${i}" value="${item.name}">
            <input type="hidden" name="item_price_${i}" value="${item.price}">
            <input type="hidden" name="item_quantity_${i}" value="${item.quantity}">
        `;
    }
}

// Ensure cart data is updated before submitting
document.getElementById("checkout-form").addEventListener("submit", function () {
    updateCartForm();
});