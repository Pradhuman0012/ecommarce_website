# Generated by Django 4.1.2 on 2023-01-03 16:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0015_rename_book_name_comment_book_record'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='book_record',
            new_name='book',
        ),
    ]
