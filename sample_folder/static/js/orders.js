 // Quantity Update
function updateQuantity(button, change) {
    const input = button.parentElement.querySelector('.item-quantity');
    let quantity = parseInt(input.value);
    quantity = isNaN(quantity) ? 1 : quantity + change;
    if (quantity < 1) quantity = 1;
    input.value = quantity;
    updateTotal();
}

// Update Total Amount
function updateTotal() {
    const items = document.querySelectorAll('.item-quantity');
    let totalAmount = 0;

    items.forEach(item => {
        const price = parseFloat(item.getAttribute('data-price'));
        const quantity = parseInt(item.value);
        totalAmount += price * quantity;
    });

    document.getElementById("total-amount").textContent = `₱${totalAmount.toFixed(2)}`;
}

// Remove Item
const removeButtons = document.querySelectorAll('.btn-remove');
removeButtons.forEach(button => {
    button.addEventListener('click', function () {
        const item = this.closest('.col-12');
        item.remove();
        updateTotal();
    });
});

document.addEventListener('DOMContentLoaded', updateTotal);