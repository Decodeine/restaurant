from django.http import HttpResponse,JsonResponse
from django.shortcuts import render,redirect
from .forms import BookingForm
from .models import Menu, Category,Cart,Order,OrderItem,Deliverystatus,Rating,Booking
from rest_framework import generics
from .serializers import MenuItemSerializer, CategorySerializer,RatingSerializer,CartSerializer,OrderSerializer,OrderItemSerializer,BookingSerializer
from rest_framework import permissions
from django.contrib.auth.models import User,Group
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.utils import timezone
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
from django.http import Http404
from rest_framework.views import APIView
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required 
from rest_framework.permissions import BasePermission
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from restaurant.utils import get_user_orders,get_or_create_cart_entry,YourPaginationClass
from .perm import IsManager,IsManagerOrReadOnly,IsDeliveryCrew,IsOrderOwner






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



@csrf_exempt
def bookings(request):
    if request.method == 'POST':
        data = json.load(request)
        exist = Booking.objects.filter(reservation_date=data['reservation_date']).filter(
            reservation_slot=data['reservation_slot']).exists()
        if not exist:
            # Get the user making the reservation
            user = request.user

            # Retrieve the menu based on the provided menu_id (adjust the key based on your actual data structure)
            menu_id = data.get('menu', None)
            menu = Menu.objects.get(id=menu_id) if menu_id else None


            #selected_time = ...  # get this value based on frontend logic
            


            # Create the Booking object with user and menu
            booking = Booking(
                user=user,
                first_name=data['first_name'],
                reservation_date=data['reservation_date'],
                reservation_slot=data['reservation_slot'],
                menu=menu,
                #reservation_time=selected_time,  # User-selected time for the reservation
                 #expiration_time=selected_time + timedelta(hours=1)  
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

    # Serialize the Booking objects
    booking_json = serializers.serialize('json', bookings)

    # Modify the serialized data to include the menu name and user name
    booking_data = json.loads(booking_json)
    for entry in booking_data:
        fields = entry['fields']

        # Replace menu ID with menu name
        menu_id = fields['menu']
        if menu_id:
            menu_name = Menu.objects.get(id=menu_id).name
            fields['menu'] = menu_name

        # Replace user ID with username
        user_id = fields['user']
        if user_id:
            user_name = User.objects.get(id=user_id).username
            fields['user'] = user_name

    # Convert back to JSON and return the response
    return HttpResponse(json.dumps(booking_data), content_type='application/json')

def booking(request):
    date = request.GET.get('date', datetime.today().date())
    user = request.user if request.user.is_authenticated else None

    # Make a request to the 'bookings' view to get the booking data
    response = bookings(request)
    
    if response.status_code == 200:
        # Parse the JSON content
        try:
            booking_data = json.loads(response.content)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Unable to parse booking data'})
        

        # Process the JSON data as needed for rendering
        processed_data = [
            {
                'first_name': item['fields']['first_name'],
                'reservation_date': item['fields']['reservation_date'],
                'reservation_slot': item['fields']['reservation_slot'],
            }
            for item in booking_data
        ]
        
        return render(request, 'bookings.html', {'booking_data': processed_data})
    else:
        # Handle the case where the 'bookings' view returns an error
        return JsonResponse({'error': 'Unable to fetch booking data'})





def menu_data(request):
    categories = Category.objects.values_list('title', flat=True).distinct()
    menus = Menu.objects.all()

    category_menu_data = {
        'categories': list(categories),
        'menus': [{'id': menu.id, 'name': menu.name, 'category': menu.category.title} for menu in menus],
    }

    # Use DjangoJSONEncoder to handle serialization of additional types
    return JsonResponse(category_menu_data, encoder=DjangoJSONEncoder)






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









class CartMenuItemsView(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def get(self, request, *args, **kwargs):
        cart_items = Cart.objects.filter(user=request.user).order_by('-created_at')
        cart_total = sum(item.price for item in cart_items)

        context = {'cart_items': cart_items, 'cart_total': cart_total}
        return render(request, 'cart.html', context)

    def perform_create(self, serializer):
        menu_item = serializer.validated_data['menu']
        cart_entry, new_entry_created = get_or_create_cart_entry(self.request.user, menu_item)
        status_code = status.HTTP_201_CREATED if new_entry_created else status.HTTP_200_OK
        serializer = CartSerializer(cart_entry)
        return Response(serializer.data, status=status_code)

    def delete(self, request, *args, **kwargs):
        # Delete all menu items created by the current user
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    

class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart_item_id = self.kwargs['pk']
        user = self.request.user

        try:
            cart_item = Cart.objects.get(pk=cart_item_id, user=user)
            return cart_item
        except Cart.DoesNotExist:
            raise Http404("Cart item does not exist or does not belong to the user.")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        quantity_change = request.data.get('quantity_change', 0)

        if not isinstance(quantity_change, int):
            return Response({'error': 'Invalid quantity change.'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the quantity
        instance.quantity += quantity_change

        # Check if the updated quantity is zero, and delete the item from the cart
        if instance.quantity <= 0:
            instance.delete()
            return Response({'message': 'Item deleted from the cart.'}, status=status.HTTP_204_NO_CONTENT)
        else:
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)





class OrderListView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_user_orders(self):
        user = self.request.user
        if user.groups.filter(name='manager').exists():
            # If the user is a manager, return all orders
            return Order.objects.all().order_by('-time')
        else:
            # If the user is not a manager, return orders for that user
            return get_user_orders(self.request).order_by('-time')

    def get_queryset(self):
        return self.get_user_orders()

    def perform_create(self, serializer):
        # Retrieve current cart items for the current user
        cart_items = Cart.objects.filter(user=self.request.user)

        # Check if the cart is not empty
        if not cart_items.exists():
            raise PermissionDenied({'error': 'Cart is empty'})

        # Calculate total price based on cart items
        total_price = sum(cart_item.price for cart_item in cart_items)

        delivery_option = self.request.data.get('delivery_option', 'SelfPickUp')

        # Set delivery_status based on delivery_option
        delivery_status = 'Pending' if delivery_option == 'Delivery' else None

        # Create a new order
        order = Order.objects.create(
            user=self.request.user,
            total=total_price,
            time=datetime.now(),
            delivery_status=delivery_status,
            delivery_option=delivery_option,
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

        # Set the created order as the serializer instance
        serializer.instance = order

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get(self, request, *args, **kwargs):
        orders = self.get_queryset()
        return render(request, 'order.html', {'orders': orders})


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsOrderOwner | IsManagerOrReadOnly | IsDeliveryCrew | IsManager | IsAuthenticated]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Check if a manager or delivery crew is updating the order
        if request.user.groups.filter(name='manager').exists():
            # Only managers can assign a delivery crew
            self.check_manager_permissions(serializer.validated_data)
        elif request.user.groups.filter(name='delivery_crew').exists():
            # Delivery crew can update the delivery_status field
            self.check_delivery_crew_permissions(serializer.validated_data)
        else:
            # Users/customers can only update the order without assigning a delivery crew
            serializer.validated_data.pop('delivery_status', None)

        # Allow updating other fields (like status) for all user groups
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        # Check if the user has permission to delete the order
        self.check_manager_permissions()
        # Perform additional actions before deleting the order
        instance.delete()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if the user has permission to delete the order
        self.check_manager_permissions()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_user_orders(self):
        return get_user_orders(self.request).order_by('-time')

    def get_queryset(self):
        return self.get_user_orders()

    def get_permissions(self):
        return super().get_permissions()

    def check_manager_permissions(self, validated_data=None):
        if validated_data and 'delivery_status' in validated_data and validated_data['delivery_status'] is not None:
            raise PermissionDenied("Managers can only update the status or assign a delivery crew.")

    def check_delivery_crew_permissions(self, validated_data=None):
        if validated_data and 'delivery_status' in validated_data:
            # Additional logic for handling status updates by delivery crew
            # You may want to add more conditions or validation here
            pass
        else:
            # Delivery crew cannot update the delivery_status field
            validated_data.pop('delivery_status', None)


@api_view(['GET'])
@permission_classes([IsManager])
def delivery_crew_list(request):
    # Retrieve all users who belong to the 'delivery_crew' group
    delivery_crew_users = User.objects.filter(groups__name='delivery_crew')

    # Extract data from User and Deliverystatus models
    crew_data = [
        {
            'id': user.delivery_crew.id if hasattr(user, 'delivery_crew') else None,
            'name': user.delivery_crew.name if hasattr(user, 'delivery_crew') else None,
            'is_available': user.delivery_crew.is_available if hasattr(user, 'delivery_crew') else None
        }
        for user in delivery_crew_users
    ]

    return Response(crew_data)


@api_view(['PUT'])
@permission_classes([IsManager])
def assign_delivery_crew(request, order_id):
    # Extract delivery crew ID from the request data
    delivery_crew_id = request.data.get('delivery_crew_id')

    # Retrieve the order and delivery crew objects
    order = get_object_or_404(Order, pk=order_id)
    delivery_crew = get_object_or_404(Deliverystatus, pk=delivery_crew_id)

    # Ensure the order is pending before assigning a delivery crew
    if order.order_status == 'Pending Assignment':
        # Check if the delivery crew is available
        if delivery_crew.is_available:
            # Update the associated user's delivery_crew field
            user = User.objects.filter(deliverystatus=delivery_crew).first()
            if user:
                user.deliverystatus = None
                user.save()

            # Assign the delivery crew to the order
            order.deliverystatus = delivery_crew
            order.order_status = 'Assigned'  # Update the order status
            order.save()

            return Response({'success': 'Delivery crew assigned successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Selected delivery crew is not available'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Order must be pending to assign a delivery crew'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsManager])
def mark_delivered(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    # Ensure the order is assigned before marking as delivered
    if order.order_status == 'Assigned':
        # Update the associated user's delivery_crew field
        user = User.objects.filter(delivery_crew=order.delivery_crew).first()
        if user:
            user.delivery_crew = None
            user.save()

        order.order_status = 'Delivered'
        order.save()
        return Response({'success': 'Order marked as delivered successfully'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Order must be assigned to mark as delivered'}, status=status.HTTP_400_BAD_REQUEST)

#@method_decorator(login_required, name='dispatch')
#class AssignDeliveryCrewView(View):
    template_name = 'assign_delivery_crew.html'

    def get(self, request, order_id):
        # You can perform any necessary checks here before rendering the template
        # For example, check if the user is a manager

        # Pass the order_id to the template
        context = {'order_id': order_id}
        return render(request, self.template_name, context)
        



def checkout(request):
    # Retrieve cart items for the current user
    cart_items = Cart.objects.filter(user=request.user)

    # Calculate total price
    total_price = sum(item.menu.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        
        order_time = timezone.now()

        # Create an order locally in the Django database
        order = Order.objects.create(user=request.user, total=total_price,time=order_time) #status='True')

        # Move cart items to the order
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu=cart_item.menu,
                quantity=cart_item.quantity,
                unit_price=cart_item.menu.price,
                price=cart_item.menu.price * cart_item.quantity
            )

        # Clear the user's cart
        cart_items.delete()

        
        
        return HttpResponse('Order successful!')

    return render(request, 'checkout.html', {'cart_items': cart_items, 'total_price': total_price})

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
    if request.method == 'GET':
        # Retrieve all users in the 'delivery_crew' group
        delivery_crew = DeliveryCrew.objects.all()
        delivery_crew_data = [{'id': crew.id, 'name': crew.name, 'is_available': crew.is_available} for crew in delivery_crew]
        return Response(delivery_crew_data)

    elif request.method == 'POST':
        # Assign the user in the payload to the 'delivery_crew' group
        try:
            crew_name = request.data['name']
            is_available = request.data.get('is_available', True)

            # Create a new delivery crew with the provided information
            new_crew = DeliveryCrew.objects.create(name=crew_name, is_available=is_available)

            return Response({'success': 'Delivery crew added successfully'}, status=status.HTTP_201_CREATED)
        except KeyError:
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsManagerOrReadOnly])
def remove_delivery_crew_user(request, crew_id):
    # Remove the crew with the given crew_id
    crew = get_object_or_404(DeliveryCrew, pk=crew_id)
    crew.delete()
    return Response({'success': 'Delivery crew removed successfully'}, status=status.HTTP_200_OK)





