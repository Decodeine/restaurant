from rest_framework import serializers
from .models import Menu,Category,Rating
from rest_framework.validators import UniqueValidator
import bleach
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth.models import User
from .models import Cart
from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['menu', 'quantity', 'unit_price', 'price']

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'order_items', 'status', 'delivery_crew']

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menu', 'quantity', 'unit_price', 'price']
        read_only_fields = ['id', 'user']  





class RatingSerializer (serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Rating
        fields = ['user', 'menuitem_id', 'rating']

        validators = [
            UniqueTogetherValidator(
                queryset=Rating.objects.all(),
                fields=['user', 'menuitem_id']
            )
        ]

        extra_kwargs = {
            'rating': {'min_value': 0, 'max_value':5},
        }




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
