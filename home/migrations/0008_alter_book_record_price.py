# Generated by Django 4.1.2 on 2022-11-03 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0007_book_record'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book_record',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
    ]