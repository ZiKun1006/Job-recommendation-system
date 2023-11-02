from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
import datetime

# Create your models here.
class student(models.Model):
    category=(('male','Male'),('female','Female'),)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name=models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    dob = models.DateField()
    gender = models.CharField(max_length=10,choices=category)
    email= models.CharField(max_length=200)
    resume=models.FileField(null=True)
    def __str__(self):
        return self.name

class company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name=models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    image = models.ImageField(upload_to="",null=True)
    email= models.CharField(max_length=200)
    website=models.URLField(max_length=200,null=True)
    avg_rating=models.FloatField(default=0,null=True)
    def __str__ (self):
        return self.name
    
    def length(self):
        return len(self.review.all())
    
class job(models.Model):
    time=(('Full time','Full Time'),('Part time','Part time'),('Internship','Internship'),('Remote','Remote'))
    company = models.ForeignKey(company, on_delete=models.CASCADE)
    expired_date = models.DateField()
    title = models.CharField(max_length=200)
    salary = models.FloatField()
    description = models.TextField(max_length=1000000000000000)
    experience = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    skills = models.TextField(max_length=1000000000000000)
    other = models.TextField(max_length=100000000000000)
    time=models.CharField(max_length=30,choices=time)
    creation_date = models.DateField()
    def __str__ (self):
        return self.title

    def checktoday(self):
        return (datetime.date.today()-self.creation_date).days < 1
    
class applyjob(models.Model):
    choice=(("Pending","Pending"),("Received","Received"),("Rejected","Rejected"))
    company = models.CharField(max_length=200)
    job = models.ForeignKey(job, on_delete=models.CASCADE)
    applicant = models.ForeignKey(student, on_delete=models.CASCADE)
    resume = models.ImageField(upload_to="")
    apply_date = models.DateField()
    status=models.CharField(max_length=20,choices=choice,default="Pending")
    def __str__ (self):
        return str(self.applicant)

class user_type(models.Model):
    is_company = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        if self.is_student == True:
            return User.get_username(self.user) + " - is_student"
        else:
            return User.get_username(self.user) + " - is_comapny"

class review(models.Model):
    company=models.ForeignKey(company, related_name='review',on_delete=models.CASCADE)
    student=models.ForeignKey(student, on_delete=models.CASCADE)
    head=models.CharField(max_length=100)
    good=models.TextField(max_length=200000)
    bad=models.TextField(max_length=2000000,default="")
    additional=models.TextField(max_length=2000000,default="-")
    score=models.IntegerField(default=0)
    creation_date = models.DateField()
    def __str__(self):
        return str(self.company)
    
class feedback(models.Model):
    email=models.CharField(max_length=200)
    title=models.CharField(max_length=200)
    content=models.TextField(max_length=200000000)
    created_date=models.DateField()
    def __str__(self):
        return self.title 
    
class searchTerm(models.Model):
    user=models.ForeignKey(student,on_delete=models.CASCADE)
    name=models.CharField(max_length=1000000)
    location=models.CharField(max_length=1000000)
    def __str__(self):
        return str(self.user)
    
class CareerTest(models.Model):
    user=models.ForeignKey(student,on_delete=models.CASCADE)
    q1=models.CharField(max_length=500)
    q2=models.CharField(max_length=500)
    q3=models.CharField(max_length=500)
    q4=models.CharField(max_length=500)
    q5=models.CharField(max_length=500)
    q6=models.CharField(max_length=500)
    q7=models.CharField(max_length=500)
    q8=models.CharField(max_length=500)
    q9=models.CharField(max_length=500)
    q10=models.CharField(max_length=500)
    q11=models.CharField(max_length=500)
    q12=models.CharField(max_length=500)
    q13=models.CharField(max_length=500)
    q14=models.CharField(max_length=500)
    q15=models.CharField(max_length=500)
    q16=models.CharField(max_length=500)
    q17=models.CharField(max_length=500)
    q18=models.CharField(max_length=500)
    q19=models.CharField(max_length=500)
    q20=models.CharField(max_length=500)
    def __str__(self):
        return str(self.user)