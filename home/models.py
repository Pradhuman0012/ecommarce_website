from statistics import mode
from django.db import models
from django.utils import timezone


# Create your models here.
class contectEnquery(models.Model):
    phone = models.CharField(max_length=122)
    email = models.CharField(max_length=122)
    password = models.CharField(max_length=122)
    user_name = models.CharField(max_length=100)
    def __str__(self) -> str:
        return self.user_name
  
class authentic(models.Model):
    email= models.CharField(max_length=112)
    password=models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.email


class Book_record(models.Model):
    book_name = models.CharField(max_length=122)
    auther = models.CharField(max_length=30)
    publication = models.CharField(max_length=50)
    no_of_pages = models.CharField(max_length=122)
    published_year =models.CharField(max_length=122)
    condition= models.CharField(max_length=50)
    book_image=models.ImageField(null=True, blank=True, upload_to="images/")
    book_file=models.FileField(null=True, blank=True, upload_to="Files/")
    price=models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self) -> str:
        return self.book_name +' - '+self.auther   


# comment section
class comment(models.Model):
    book=models.ForeignKey(Book_record,related_name='comments',on_delete=models.CASCADE)
    name=models.CharField(max_length=50)
    email=models.EmailField()
    body=models.TextField()
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    active=models.BooleanField(default=True)
    class Mets:
        ordering=('-created',)
    def __str__(self):
         return f"Commented by {self.name} on {self.book_name}."