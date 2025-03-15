var editItemModal = document.getElementById('editItemModal');
    editItemModal.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget;
        var itemId = button.getAttribute('data-id');
        var itemName = button.getAttribute('data-name');
        var itemPrice = button.getAttribute('data-price');
        var itemQuantity = button.getAttribute('data-quantity');
        
        document.getElementById('editItemId').value = itemId;
        document.getElementById('editItemName').value = itemName;
        document.getElementById('editItemPrice').value = itemPrice;
        document.getElementById('editItemQuantity').value = itemQuantity;
    });

