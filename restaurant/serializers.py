from rest_framework import serializers
from .models import Menu,Category
from rest_framework.validators import UniqueValidator
import bleach


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['title']

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Menu
        fields = ['id', 'name', 'price', 'inventory', 'menu_item_description', 'category']
        extra_kwargs = {
            'price': {'min_value': 2},
            'inventory': {'min_value': 0},
            'name': {'validators': [UniqueValidator(queryset=Menu.objects.all())]}
        }

    def validate(self, attrs):
        attrs['name'] = bleach.clean(attrs['name'])
        if attrs['price'] < 2:
            raise serializers.ValidationError('Price should not be less than 2.0')
        if attrs['inventory'] < 0:
            raise serializers.ValidationError('Stock cannot be negative')
        return super().validate(attrs)
