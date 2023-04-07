from django import forms
from .models import Book_record,comment

class book_recordForm(forms.ModelForm):
    
    class Meta:
        model = Book_record
        fields = ("book_name","auther","publication","no_of_pages","published_year","condition","price","book_image","book_file")
        labels={
            "book_name":"",
            "auther":"",
            "publication":"",
            "no_of_pages":"",
            "published_year":"",
            "condition":"",
            "book_image":"Book cover",
            "book_file":"Book file",
            "price":""
        }
        widgets={
            "book_name": forms.TextInput(attrs={'class':'form-control','placeholder':'Book name'}),
            "auther": forms.TextInput(attrs={'class':'form-control','placeholder':'Auther'}),
            "publication": forms.TextInput(attrs={'class':'form-control','placeholder':'Publication'}),
            "no_of_pages": forms.TextInput(attrs={'class':'form-control','placeholder':'No of pages'}),
            "published_year": forms.TextInput(attrs={'class':'form-control','placeholder':'Published year'}),
            "condition": forms.TextInput(attrs={'class':'form-control','placeholder':'Condition'}),
            "book_image": forms.FileInput(attrs={'class':'form-control'}),
            "book_file": forms.FileInput(attrs={'class':'form-control'}),
            
            "price": forms.TextInput(attrs={'class':'form-control','placeholder':'Price'})
        }


class commentForm(forms.ModelForm):
    class Meta:
        model=comment
        fields=('name','email','body')