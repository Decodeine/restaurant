# Generated by Django 4.2.5 on 2023-12-09 05:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0007_alter_booking_menu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='menu',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='restaurant.menu'),
            preserve_default=False,
        ),
    ]
