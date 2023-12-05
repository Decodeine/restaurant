# utils.py

from rest_framework.response import Response
from rest_framework import status
from .models import Cart

def get_or_create_cart_entry(user, menu_item):
    existing_cart_entry = Cart.objects.filter(user=user, menu=menu_item).first()

    if existing_cart_entry:
        # Update the quantity if the cart entry already exists
        existing_cart_entry.quantity += 1
        existing_cart_entry.save()
        return existing_cart_entry, False  # Entry already existed
    else:
        # Create a new cart entry if it doesn't exist
        new_cart_entry = Cart.objects.create(user=user, menu=menu_item, quantity=1)
        return new_cart_entry, True  # New entry created
