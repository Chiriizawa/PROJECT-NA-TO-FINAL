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
