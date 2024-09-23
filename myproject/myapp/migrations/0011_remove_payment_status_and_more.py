# Generated by Django 5.1.1 on 2024-09-23 00:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_backup_bill_backup_status_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='status',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='subscription_plan',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='transaction_id',
        ),
        migrations.AddField(
            model_name='payment',
            name='card_number',
            field=models.CharField(default=4567, max_length=16),
        ),
    ]
