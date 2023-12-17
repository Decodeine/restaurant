# Generated by Django 4.2.5 on 2023-12-14 09:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('restaurant', '0016_remove_order_delivery_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliverycrew',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='delivery_crew', to=settings.AUTH_USER_MODEL),
        ),
    ]
