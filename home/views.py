from django.shortcuts import render
from django.views.generic import ListView,DetailView
from home.models import Book_record,contectEnquery,authentic
from home.forms import book_recordForm,commentForm
from django.shortcuts import render,get_list_or_404,get_object_or_404
from django.http import HttpResponseRedirect
# Create your views here.
# class homeView(ListView):
#     model=Book_record
#     template_name='home/index.html'
####################
def homeView(request):
    book_list=Book_record.objects.all()
    return render(request,'home/index.html',{'book_list':book_list})
####################


# class shopView(DetailView):
#     model=Book_record
#     context_object_name='book'
#     template_name="home/shop.html"

######################

def shopView(request,pk):
    book=get_object_or_404(Book_record,pk=pk)
    book_list=Book_record.objects.all()
    comments=book.comments.filter(active=True)
    csubmit=False
    if request.method=='POST':
        form=commentForm(request.POST)
        if form.is_valid():
            new_comment=form.save(commit=False)
            new_comment.book=book
            new_comment.save()
            csubmit=True    
    else:
        form=commentForm()
    return render(request,'home/shop.html',{'book':book,'form':form,'csubmit':csubmit,'comments':comments,'book_list':book_list})
######################

def about(request):
    return render(request,'about.html')

def checkout(request):
    return render(request,'home/checkout.html')

def searchBook(request):
    if request.method=="POST":
        searched=request.POST['searched']
        book=Book_record.objects.filter(book_name__contains=searched)
        return render(request,'home/search.html',
        {'searched':searched,
         'Book_record_list':book
        })    
    else:
        return render(request,'home/search.html',{})


def tranding(request):
    if request.method=='POST':
        mail=request.POST.get('email')
        password=request.POST.get('password')
        data=authentic(email=mail,password=password)
        data.save()
    return render(request,'tranding.html')
def shop(request):
    book_rec= Book_record.objects.all()
    return render(request,"shop.html",
    {'book_rec':book_rec})
def login(request):
    if request.method =='POST':
        phone=request.POST.get('phone')
        email=request.POST.get('email')
        password=request.POST.get('password')
        user_name=request.POST.get('user_name')
        data=contectEnquery(phone=phone,email=email,password=password,user_name=user_name)
        data.save()
    return render(request,"loginpage.html")
# def home(request):
#     return render(request,"index.html")
def storedata(request):
    submitted=False
    if request.method=="POST":
        form=book_recordForm(request.POST,request.FILES)
        form.save()
        return HttpResponseRedirect('/storedata?submitted=True')
    else:
        form=book_recordForm
        if 'submitted' in request.GET:
            submitted = True

    return render(request,"storedata.html",{'form':form,'submitted':submitted})

    