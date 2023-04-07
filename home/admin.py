from django.contrib import admin
from home.models import contectEnquery
from home.models import authentic
from home.models import Book_record,comment
# Register your models here.

class commentAdmin(admin.ModelAdmin):
    list_display=['book','name','email','body','created','updated','active']
    # list_filter=('created','updated','active')
    # ordering=['created','updated','active']
    # search_fields=['name','email']
admin.site.register(comment,commentAdmin)


admin.site.register(contectEnquery)
admin.site.register(authentic)
admin.site.register(Book_record)

