from rest_framework import serializers
from .models import Menu


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ['id','name','price','inventory','menu_item_description']
        extra_kwargs = {
            'price': {'min_value': 2},
            'inventory':{'min_value':0}
        }