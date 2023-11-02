from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(student)
admin.site.register(company)
admin.site.register(job)
admin.site.register(applyjob)
admin.site.register(user_type)
admin.site.register(review)
admin.site.register(feedback)
admin.site.register(searchTerm)
admin.site.register(CareerTest)