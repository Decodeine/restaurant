from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone




class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem_id =  models.SmallIntegerField()
    rating = models.SmallIntegerField()


'''class Booking(models.Model):
   first_name = models.CharField(max_length=200)    
   last_name = models.CharField(max_length=200)
   guest_number = models.IntegerField()
   comment = models.CharField(max_length=1000)

   def __str__(self):
      return self.first_name + ' ' + self.last_name'''


    
class Bookings(models.Model):
    name = models.CharField(max_length=255)
    number_of_guests = models.IntegerField()
    booking_date =models.DateTimeField()

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Booking Records'

    def __str__(self) -> str:
        return f'{self.name} for {self.number_of_guests} guests on {self.booking_date}'



class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=True)
    id = models.AutoField(primary_key=True)

    def __str__(self) -> str:
        return self.title

class Menu(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    id = models.AutoField(primary_key=True) 
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    menu_item_description = models.TextField(max_length=1000, default='')  # Specify a max_length
    inventory = models.SmallIntegerField(db_index=True)
    featured = models.BooleanField(db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return self.name
    
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    first_name = models.CharField(max_length=200)
    reservation_date = models.DateField()
    reservation_slot = models.SmallIntegerField(default=10)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    #reservation_time = models.DateTimeField()
    #expiration_time = models.DateTimeField()

    def __str__(self): 
        return self.first_name



class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, editable=False)
    price = models.DecimalField(max_digits=6, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('menu', 'user')

    def save(self, *args, **kwargs):
        # Set unit_price based on the associated menu item
        self.unit_price = self.menu.price

        # Calculate total price based on quantity
        self.price = self.unit_price * self.quantity

        super().save(*args, **kwargs)




class Deliverystatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    DELIVERY_STATUS_CHOICES = [
        ('Delivery', 'Delivery'),
        ('SelfPickUp', 'Self Pick Up'),
        ('Pending', 'Pending Assignment'),
    ]
    delivery_status = models.CharField(
        max_length=20, choices=DELIVERY_STATUS_CHOICES
    )
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_status = models.ForeignKey(Deliverystatus, null=True, blank=True, on_delete=models.SET_NULL)
    time = models.DateTimeField()

    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending Assignment'),
        ('Assigned', 'Assigned'),
        ('Delivered', 'Delivered'),
    ]

    order_status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default='Pending'
    )

    total = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Order ({self.date}{self.time}))"


class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE)
    menu= models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity=models.SmallIntegerField()
    unit_price=models.DecimalField(max_digits=6,decimal_places=2)
    price=models.DecimalField(max_digits=6,decimal_places=2)

    class Meta:
        unique_together=('order', 'menu')



