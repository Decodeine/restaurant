from django.http import HttpResponse,JsonResponse
from django.shortcuts import render,redirect
from .forms import BookingForm
from .models import Menu, Category,Cart,Order,OrderItem
from rest_framework import generics
from .serializers import MenuItemSerializer, CategorySerializer,RatingSerializer,CartSerializer,OrderSerializer,OrderItemSerializer,BookingSerializer
from rest_framework.pagination import PageNumberPagination
from .models import Rating,Booking
from rest_framework import permissions
from django.contrib.auth.models import User,Group
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from rest_framework.response import Response
from rest_framework import status, viewsets,generics
from django.shortcuts import get_object_or_404
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.exceptions import PermissionDenied
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json
from django.views import View
import requests
from djoser.views import TokenCreateView
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login


class CustomTokenCreateView(View):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            # If the credentials are correct, log in the user
            login(request, user)

            # Redirect to a secure and trusted URL after successful login
            return redirect('restaurant:home')
        else:
            # If the credentials are incorrect, provide an error message
            return render(request, self.template_name, {'error_message': 'Incorrect credentials. Please try again.'})

class RegistrationView(View):
    template_name = 'registration.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        # Extract user registration data from the form
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Djoser registration endpoint URL
        djoser_registration_url = 'http://localhost:8000/api/users/'

        # Data to be sent to Djoser registration endpoint
        registration_data = {
            'email': email,
            'username': username,
            'password': password,
        }

        # Make a POST request to Djoser registration endpoint
        response = requests.post(djoser_registration_url, data=registration_data)

        # Check the response from Djoser
        if response.status_code == 201:  # Successful registration
            return render(request, self.template_name, {'success_message': 'Registration successful'})
        else:  # Registration failed
            return render(request, self.template_name, {'error_message': response.text})



def home(request):
    print(f"Request headers: {request.headers}")

    print(f"Session data: {request.session.items()}")
    print(f"User: {request.user}")
    print(f"Is authenticated? {request.user.is_authenticated}")

    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')





class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.groups.filter(name='manager').exists()

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.groups.filter(name='manager').exists()


class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def list(self, request, *args, **kwargs):
        # Print statement to check if the session token is present in the headers
        print(f"Request Headers: {request.headers}")

        return super().list(request, *args, **kwargs)



def book(request):
    form = BookingForm()
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
    context = {'form': form}
    return render(request, 'book.html', context)

from django.contrib.auth.decorators import user_passes_test

@csrf_exempt
def bookings(request):
    if request.method == 'POST':
        data = json.load(request)
        exist = Booking.objects.filter(reservation_date=data['reservation_date']).filter(
            reservation_slot=data['reservation_slot']).exists()
        if exist == False:
            booking = Booking(
                first_name=data['first_name'],
                reservation_date=data['reservation_date'],
                reservation_slot=data['reservation_slot'],
            )
            booking.save()
        else:
            return HttpResponse("{'error':1}", content_type='application/json')

    date = request.GET.get('date', datetime.today().date())

    # Check if the user is a manager
    if request.user.is_staff:
        # If the user is a manager, return all bookings
        bookings = Booking.objects.all().filter(reservation_date=date)
    else:
        # If the user is not a manager, return only the user's bookings
        bookings = Booking.objects.filter(reservation_date=date, user=request.user)

    booking_json = serializers.serialize('json', bookings)

    return HttpResponse(booking_json, content_type='application/json')





class YourPaginationClass(PageNumberPagination):
    page_size = 5  # Number of items per page
    page_size_query_param = 'page'
    max_page_size = 50


class MenuItemsView(generics.ListCreateAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price', 'inventory']
    filterset_fields = ['price', 'inventory']
    search_fields = ['name']
    pagination_class = YourPaginationClass
    permission_classes = [IsManagerOrReadOnly]

    def get(self, request, *args, **kwargs):
        menu_items = self.get_queryset()
        print("Primary keys of menu items:", [item.pk for item in menu_items])

        serializer = self.get_serializer(menu_items, many=True)
        
        return render(request, 'menu.html', {'menu_items': serializer.data})


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]  

    def get(self, request, *args, **kwargs):
        menu_item = self.get_object()
        serializer = self.get_serializer(menu_item)
        return render(request, 'menu_item.html', {'menu_item': serializer.data})

    
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class RatingsView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

    def get_permissions(self):
        if(self.request.method=='GET'):
            return []

        return [IsAuthenticated()]
    

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


class CartAddItemView(generics.CreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        menu_item_id = request.data.get('menu')
        quantity = request.data.get('quantity', 1)

        if not menu_item_id:
            return Response({'error': 'Menu item ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            menu_item = Menu.objects.get(id=menu_item_id)
        except Menu.DoesNotExist:
            return Response({'error': 'Menu item not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Validate quantity
        if not isinstance(quantity, int) or quantity <= 0:
            return Response({'error': 'Invalid quantity.'}, status=status.HTTP_400_BAD_REQUEST)

        # Use the helper function to get or create a cart entry
        cart_entry, new_entry_created = get_or_create_cart_entry(request.user, menu_item)

        # Adjust the response based on whether a new entry was created
        status_code = status.HTTP_201_CREATED if new_entry_created else status.HTTP_200_OK

        serializer = CartSerializer(cart_entry)
        return Response(serializer.data, status=status_code)





class CartMenuItemsView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer
    template_name = 'cart.html'


    def get(self, request, *args, **kwargs):
        cart_items = Cart.objects.filter(user=request.user).order_by('-created_at')
        context = {'cart_items': cart_items}
        return render(request, self.template_name, context)

 

    def perform_create(self, serializer):
        menu_item = serializer.validated_data['menu']

        # Use the helper function to get or create a cart entry
        cart_entry, new_entry_created = get_or_create_cart_entry(self.request.user, menu_item)

        # Adjust the response based on whether a new entry was created
        status_code = status.HTTP_201_CREATED if new_entry_created else status.HTTP_200_OK

        serializer = CartSerializer(cart_entry)
        return Response(serializer.data, status=status_code)
    
    def destroy(self, request, *args, **kwargs):
        # Delete all menu items created by the current user
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class IsDeliveryCrew(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='delivery_crew').exists()
    
class IsOrderOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the order
        return obj.user == request.user
 

class OrderListView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='manager').exists():
            # Manager can see orders for all users
            return Order.objects.all()
        elif user.groups.filter(name='delivery_crew').exists():
            # Delivery crew can see all orders assigned to them
            return Order.objects.filter(delivery_crew=user)

        else:
            # Customers can see only their orders
            return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        # Retrieve current cart items for the current user
        cart_items = Cart.objects.filter(user=self.request.user)

        # Check if the cart is not empty
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total price based on cart items
        total_price = sum(cart_item.price for cart_item in cart_items)

        # Create a new order
        order = Order.objects.create(
            user=self.request.user,
            # status=True,  # Set your default status here
            total=total_price,  # Set your default total here
            # You may need to set other fields like delivery_crew, date, etc.
        )

        # Create order items based on cart items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu=cart_item.menu,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                price=cart_item.price,
            )

        # Delete all items from the cart for this user
        cart_items.delete()
        
        # Set the order status based on conditions
        self.set_order_status(order)

        # Set the created order as the serializer instance
        serializer.instance = order

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def set_order_status(self, order):
        # Additional logic for setting the status based on conditions
        # For example, you might want to set the status to 'out for delivery' if a delivery_crew is assigned
        if order.delivery_crew and order.status is None:
            order.status = 0
            order.save()



class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsOrderOwner | IsManagerOrReadOnly | IsDeliveryCrew]

    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Check if a manager or delivery crew is updating the order
        if request.user.groups.filter(name='manager').exists():
            # Only managers can assign a delivery crew
            if 'delivery_crew' in serializer.validated_data and serializer.validated_data['delivery_crew'] is not None:
                raise PermissionDenied("Managers can only update the status or assign a delivery crew.")
        elif request.user.groups.filter(name='delivery_crew').exists():
            # Delivery crew can update the status field
            if 'status' in serializer.validated_data:
                # Additional logic for handling status updates by delivery crew
                # You may want to add more conditions or validation here
                pass
            else:
                # Delivery crew cannot update the delivery_crew field
                serializer.validated_data.pop('delivery_crew', None)
        else:
            # Users/customers can only update the order without assigning a delivery crew
            serializer.validated_data.pop('delivery_crew', None)

        # Allow updating other fields (like status) for all user groups
        self.perform_update(serializer)
        return Response(serializer.data)
    def perform_destroy(self, instance):
        # Check if the user has permission to delete the order
        if not self.request.user.groups.filter(name='manager').exists():
            raise PermissionDenied("You do not have permission to delete this order.")
        
        # Perform additional actions before deleting the order
        instance.delete()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if the user has permission to delete the order
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='manager').exists():
            # Manager can see orders for all users
            return Order.objects.all()
        elif user.groups.filter(name='delivery_crew').exists():
            # Delivery crew can see orders assigned to them
            return Order.objects.filter(delivery_crew=user)
        else:
            # Other users can only see their own orders
            return Order.objects.filter(user=user)
        
#class UserViewSet(viewsets.ModelViewSet):
   #queryset = User.objects.all() 
   #serializer_class = UserSerializer
   #permission_classes = [permissions.IsAuthenticated] 


@api_view(['GET', 'POST'])
@permission_classes([IsManagerOrReadOnly])
def manager_users(request):
    if request.method == 'GET':
        # Retrieve all users in the 'manager' group
        managers = User.objects.filter(groups__name='manager')
        manager_data = [{'id': manager.id, 'username': manager.username} for manager in managers]
        return Response(manager_data)

    elif request.method == 'POST':
        # Assign the user in the payload to the 'manager' group
        try:
            user_id = request.data['user_id']
            user = User.objects.get(pk=user_id)
        except (KeyError, User.DoesNotExist):
            return Response({'error': 'Invalid user_id'}, status=status.HTTP_400_BAD_REQUEST)

        manager_group, created = Group.objects.get_or_create(name='manager')
        user.groups.add(manager_group)
        return Response(status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsManagerOrReadOnly])
def remove_manager_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    manager_group = get_object_or_404(Group, name='manager')
    user.groups.remove(manager_group)
    return Response(status=status.HTTP_200_OK)



@api_view(['GET', 'POST'])
@permission_classes([IsManagerOrReadOnly])
def delivery_crew_users(request):
    # Similar implementation for 'delivery_crew' group
    if request.method == 'GET':
        # Retrieve all users in the 'delivery_crew' group
        delivery_crew = User.objects.filter(groups__name='Delivery_crew')
        delivery_crew_data = [{'id': user.id, 'username': user.username} for user in delivery_crew]
        return Response(delivery_crew_data)

    elif request.method == 'POST':
        # Assign the user in the payload to the 'delivery_crew' group
        try:
            user_id = request.data['user_id']
            user = User.objects.get(pk=user_id)
        except (KeyError, User.DoesNotExist):
            return Response({'error': 'Invalid user_id'}, status=status.HTTP_400_BAD_REQUEST)

        delivery_crew_group, created = Group.objects.get_or_create(name='Delivery_crew')
        user.groups.add(delivery_crew_group)
        return Response(status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsManagerOrReadOnly])
def remove_delivery_crew_user(request, user_id):
    # Remove the user with the given user_id from the 'delivery_crew' group
    user = get_object_or_404(User, pk=user_id)
    delivery_crew_group = get_object_or_404(Group, name='Delivery_crew')
    user.groups.remove(delivery_crew_group)
    return Response(status=status.HTTP_200_OK)




