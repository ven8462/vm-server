# Generated by Django 5.1.1 on 2024-09-22 22:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0008_subuser'),
    ]

    operations = [
        migrations.AddField(
            model_name='subuser',
            name='assigned_model',
            field=models.FloatField(default=1.0),
        ),
    ]
