# Generated by Django 2.2.8 on 2020-02-28 07:44

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0010_order_billing_address'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='BilingAddress',
            new_name='BillingAddress',
        ),
    ]