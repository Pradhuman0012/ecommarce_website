# Generated by Django 4.1.2 on 2023-01-03 16:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_comment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='book_name',
            new_name='book_record',
        ),
    ]
