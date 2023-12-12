# bookings/management/commands/check_expired_bookings.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from .models import Booking

class Command(BaseCommand):
    help = 'Check and update the status of expired bookings'

    def handle(self, *args, **options):
        current_time = timezone.now()

        # Find bookings that have expired
        expired_bookings = Booking.objects.filter(expiration_time__lt=current_time)

        # Update the status of expired bookings (e.g., set a flag indicating expiration)
        for booking in expired_bookings:
            booking.expired = True
            booking.save()

        self.stdout.write(self.style.SUCCESS('Successfully checked and updated expired bookings.'))
