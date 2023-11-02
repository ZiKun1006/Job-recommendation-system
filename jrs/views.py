from django.shortcuts import render,redirect
from .models import *
from django.contrib import messages
from django.contrib.auth import login,authenticate,logout
from datetime import date
import random
import regex
import fitz
import pandas as pd
from geopy.geocoders import Nominatim
import requests
import json

# Create your views here.
def home(request):
    List=list(job.objects.all())
    Jobs=random.sample(List,20)
    expired=job.objects.filter(expired_date=date.today())
    expired.delete() 

    if request.method == 'POST':
        if 'login' in request.POST:
            username = request.POST['email']
            password = request.POST['password']
            user=authenticate(request,username=username,password=password) 
            if user is not None:
                login(request,user)
                type=user_type.objects.get(user=user)
                if user.is_authenticated and type.is_student:
                    return redirect("user_homepage")

                elif user.is_authenticated and type.is_company:
                    return redirect("company_homepage")    
            else:
                messages.error(request,'Username is invalid or Password is incorrect!')
    else:
        username=request.session.get('email')
        password=request.session.get('password')
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            type=user_type.objects.get(user=user)
            if user.is_authenticated and type.is_student:
                return redirect("user_homepage")

            elif user.is_authenticated and type.is_company:
                return redirect("company_homepage")    
            
    if 'search' in request.POST:
        request.session['name'] = request.POST['name']
        request.session['location'] = request.POST['location']
        return redirect("search_result")

    return render(request,"home.html",{'Jobs':Jobs,'company':companies})

def signup(request):
    if request.method == "POST":
        if 's-signup' in request.POST:
            username=request.POST['username']
            email=request.POST['email']
            gender=request.POST['gender']
            dob=request.POST['dob']
            phone=request.POST['phone']
            resume=request.FILES['resume']
            psw=request.POST['psw']
            cpsw=request.POST['cpsw']

            if psw == cpsw:
                if User.objects.filter(email=email).exists():
                    messages.info(request,'Email was taken! Please use other email')
                    return redirect('signup')

                elif User.objects.filter(username=username).exists():
                    messages.info(request,'This username was taken! Please use other username')
                    return redirect('signup')

                else:
                    user = User.objects.create_user(username=username,email=email,password=psw)
                    user.save()
                    NewUser=student.objects.create(user=user,name=username,email=email,gender=gender,dob=dob,phone=phone,resume=resume)
                    NewUser.save()
                    UserType= user_type.objects.create(user=user,is_student=True)
                    UserType.save()
                    return redirect('home')
            else:
                messages.info(request,'Password Not Matching! Please Enter Again')
                return redirect('signup')

        if 'e-signup' in request.POST:
            companyname = request.POST['username']
            email = request.POST['email']
            phone = request.POST['phone']
            image = request.FILES['image']
            psw = request.POST['psw1']
            cpsw = request.POST['cpsw1']
            url=request.POST['url']

            if psw == cpsw:
                if User.objects.filter(email=email).exists(): 
                    messages.info(request,'Email was taken! Please use other email')
                    return redirect('signup')

                elif User.objects.filter(username=companyname).exists():
                    messages.info(request,'This company name was taken! Please use other company name')
                    return redirect('signup')

                else:
                    user = User.objects.create_user(username=companyname,email=email,password=psw)
                    user.save()
                    NewUser=company.objects.create(user=user,name=companyname,email=email,phone=phone,image=image,website=url)
                    NewUser.save()
                    UserType= user_type.objects.create(user=user,is_company=True)
                    UserType.save()
                    return redirect('home')
            else:
                messages.info(request,'Password Not Matching! Please Enter Again')
                return redirect('signup')

    return render(request, 'signup.html')

def forgotpsw(request):
    if request.method == "POST":
        email = request.POST['email']
        user=User.objects.filter(email=email).first()

        if not user:
            messages.error(request, 'An invalid email has been entered.')
            return redirect('forgotpsw')
            
        request.session['user']=user.username
        return redirect('password_reset')

    return render(request,"forgotpsw.html")

def password_reset(request):
    if request.method == "POST":
        new_psw=request.POST['new_password']
        new_psw_1=request.POST['new_password1']
        username=request.POST['username']
        
        if new_psw != new_psw_1:
            messages.error(request,'Both passwords are not matched!')
            return redirect('password_reset')
        
        if username == "AnonymousUser":
            username=request.session['user']

        user = User.objects.filter(username=username).first()

        user.set_password(new_psw)
        user.save()
        return redirect('resetcompleted')

    return render(request,'reset_password.html')

def companies(request):
    if request.method == "POST":
        if 'login' in request.POST:
            request.session['email'] = request.POST['email']
            request.session['password'] = request.POST['password']
            return redirect('home')
        
        if 'submit' in request.POST:
            value=request.POST['company']
            companys=list(company.objects.filter(name__icontains=value))
            reviews=list(review.objects.all().order_by('-creation_date'))
        
    else:   
        companys=list(company.objects.all())
        reviews=list(review.objects.all().order_by('-company__avg_rating'))
        
    empty_list=[]
    non_empty_list=[]
    if reviews==[]:
        for i in companys:
            empty_list.append(i)
    else:
        for rev in reviews:
            for i in companys:
                if rev.company != i:
                    if i not in empty_list:
                        empty_list.append(i)
                else:
                    if i not in non_empty_list:
                        non_empty_list.append(i)
    empty_list=[i for i in empty_list if i not in non_empty_list]       
    return render(request,"companies.html",{'company_reviews1':empty_list,'company_reviews2':non_empty_list})

def resetcompleted(request):
    return render(request,'password_reset_completed.html')

def add_job(request):
    if not request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        title=request.POST['title']
        time=request.POST['time']
        expired_date=request.POST['expired_date']
        salary=request.POST['salary']
        experience=request.POST['experience']
        skill=request.POST['skills']
        location=request.POST['location']
        description=request.POST["description"]
        others=request.POST["others"]
        username=request.POST['username']
        exist_company=company.objects.get(name=username)

        if job.objects.filter(title=title).first():
            messages.error(request,'The position has already exist in the job list!')
            return redirect('add_job')

        jobs=job.objects.create(company=exist_company,title=title,time=time,expired_date=expired_date,salary=salary,experience=experience,skills=skill,location=location,description=description,other=others,creation_date=date.today())
        jobs.save()
        return redirect('company_homepage')

    return render(request,'addjob.html')

def job_list(request):
    if not request.user.is_authenticated:
        return redirect('home')
    
    exist_company=company.objects.get(name=request.user)
    jobs=job.objects.filter(company=exist_company)
    
    return render(request,'job_list.html',{'jobs':jobs})

def company_homepage(request):
    if not request.user.is_authenticated:
        return redirect('home')
    
    companys=company.objects.get(user=request.user)
    return render(request,'company_homepage.html',{'company':companys})

def edit_job(request,id):
    if not request.user.is_authenticated:
        return redirect('home')

    Job=job.objects.get(id=id)
    if request.method == "POST":
        title=request.POST['title']
        expired_date=request.POST['expired_date']
        salary=request.POST['salary']
        experience=request.POST['experience']
        skill=request.POST['skills']
        location=request.POST['location']
        description=request.POST["description"]
        others=request.POST["others"]
        time=request.POST['time']

        Job.title=title
        Job.expired_date=expired_date
        Job.salary=salary
        Job.experience=experience
        Job.skills=skill
        Job.location=location
        Job.description=description
        Job.other=others
        Job.time=time
        Job.creation_date=date.today()
        Job.save()
        return redirect('job_list')
    return render(request,'edit_job.html',{'job':Job})

def company_profile(request):
    Company=company.objects.get(name=request.user)
    return render(request,'company_profile.html',{'company':Company})

def edit_company_profile(request):
    if not request.user.is_authenticated:
        return redirect('home')
    
    Company=company.objects.get(user=request.user)
    if request.method == "POST":
        if 'info-update' in request.POST:
            email=request.POST['email'] 
            phone=request.POST['phone']
            website=request.POST['website']

            Company.email=email
            Company.phone=phone
            Company.website=website
            Company.save()

            return redirect('company_profile')

        if 'logo-update' in request.POST:
            image = request.FILES['image']

            Company.image=image
            Company.save()
            
            return redirect('company_profile')

    return render(request,'edit_company_profile.html',{'company':Company})

def delete_job(request,id):
    if not request.user.is_authenticated:
        return redirect('home')

    Job=job.objects.get(id=id)
    Job.delete()
    return redirect('job_list')

def company_view_applicant(request):
    if not request.user.is_authenticated:
        return redirect('home')

    employee=company.objects.get(name=request.user)
    applies=applyjob.objects.filter(company=employee)
    allstudents=student.objects.all()

    if request.method=="POST":   
        if 'submit' in request.POST:
            name=request.POST['applicant']
            jobs=request.POST['jobs']
            status=request.POST['status']
            specific_job=applyjob.objects.get(applicant=student.objects.get(name=name),job=job.objects.get(title=jobs))
            specific_job.status=status
            specific_job.save()
            return redirect('company_view_applicant')
        
        if 'filter' in request.POST:
            courses=request.POST.getlist('course')
            languages=request.POST.getlist('language')
            ages=request.POST.getlist('age')
            object_list1=[]
            object_list2=[]
            final_list=[]
            
            for apply in applies:
                for students in allstudents:
                    if apply.applicant == students:
                        words=""
                        each_student=student.objects.get(name=students.name)
                        year=datetime.date.today().year-each_student.dob.year
                        pdf=fitz.open('../fyp1'+each_student.resume.url)

                        for text in pdf:
                            words+=text.get_text()
                        words=regex.sub(r'\d+',' ',words)
                        words=regex.sub('httpS+s*',' ',words)
                        words=words.strip()

                        if courses == []:
                            object_list1=None
                        else:
                            for course in courses:
                                if course=="all":
                                    if applyjob.objects.get(applicant=each_student,company=employee) not in object_list1:
                                        object_list1.append(applyjob.objects.get(applicant=each_student,company=employee))
                                        
                                elif course =="Information and Communication Technology":
                                    filterings=["Information and Communication Technology","Information Technology"]
                                    for filtering in filterings:
                                        if filtering in words:
                                            if applyjob.objects.get(applicant=each_student,company=employee) not in object_list1:
                                                object_list1.append(applyjob.objects.get(applicant=each_student,company=employee))
                                
                                elif course in words:
                                    if applyjob.objects.get(applicant=each_student,company=employee) not in object_list1:
                                        object_list1.append(applyjob.objects.get(applicant=each_student,company=employee))

                        if object_list1 ==[]:
                            final_list=[]  

                        if object_list1 == None:
                            if languages == []:
                                object_list2=None
                            else:
                                for language in languages:
                                    if language == "all":
                                        object_list2.append(applyjob.objects.get(applicant=each_student,company=employee))

                                    elif language =="english":
                                        filterings=["english","English","ENGLISH"]
                                        for filtering in filterings:
                                            if filtering in words:
                                                if applyjob.objects.get(applicant=each_student,company=employee) not in object_list2:
                                                    object_list2.append(applyjob.objects.get(applicant=each_student,company=employee))
                                    
                                    elif language =="malay":
                                        filterings=["Bahasa Malaysia","Malay","malay","MALAY"]
                                        for filtering in filterings:
                                            if filtering in words:
                                                if applyjob.objects.get(applicant=each_student,company=employee) not in object_list2:
                                                    object_list2.append(applyjob.objects.get(applicant=each_student,company=employee))

                                    elif language =="mandarin":
                                        filterings=["mandarin","MANDARIN","Mandarin"]
                                        for filtering in filterings:
                                            if filtering in words:
                                                if applyjob.objects.get(applicant=each_student,company=employee) not in object_list2:
                                                    object_list2.append(applyjob.objects.get(applicant=each_student,company=employee)) 

                        elif object_list1 !=[]: 
                            if languages == []:
                                object_list2=object_list1
                            else:
                                for language in languages:
                                    if language == "all":
                                        if applyjob.objects.get(applicant=each_student,company=employee) in object_list1:
                                            if applyjob.objects.get(applicant=each_student,company=employee) not in object_list2:
                                                object_list2.append(applyjob.objects.get(applicant=each_student,company=employee))

                                    elif language =="english":
                                        filterings=["english","English","ENGLISH"]
                                        for filtering in filterings:
                                            if filtering in words:
                                                if applyjob.objects.get(applicant=each_student,company=employee) in object_list1:
                                                    if applyjob.objects.get(applicant=each_student,company=employee) not in object_list2:
                                                        object_list2.append(applyjob.objects.get(applicant=each_student,company=employee))
                                    
                                    elif language =="malay":
                                        filterings=["Bahasa Malaysia","Malay","malay","MALAY"]
                                        for filtering in filterings:
                                            if filtering in words:
                                                if applyjob.objects.get(applicant=each_student,company=employee) in object_list1:
                                                    if applyjob.objects.get(applicant=each_student,company=employee) not in object_list2:
                                                        object_list2.append(applyjob.objects.get(applicant=each_student,company=employee))

                                    elif language =="mandarin":
                                        filterings=["mandarin","MANDARIN","Mandarin"]
                                        for filtering in filterings:
                                            if filtering in words:
                                                if applyjob.objects.get(applicant=each_student,company=employee) in object_list1:
                                                    if applyjob.objects.get(applicant=each_student,company=employee) not in object_list2:
                                                        object_list2.append(applyjob.objects.get(applicant=each_student,company=employee))

                            if object_list2==[]:
                                final_list=[] 
                        if object_list2 == None:
                            if ages == []:
                                final_list=[]
                            else:
                                for age in ages:
                                    if age=="all": 
                                        if applyjob.objects.get(applicant=each_student,company=employee) not in final_list:
                                            final_list.append(applyjob.objects.get(applicant=each_student,company=employee))
                                    elif age=="21to25":
                                        if year >= 21 and year <= 25:
                                            if applyjob.objects.get(applicant=each_student,company=employee) not in final_list:
                                                final_list.append(applyjob.objects.get(applicant=each_student,company=employee))
                                    elif age=="26to30":
                                        if year >= 26 and year <= 30:
                                            if applyjob.objects.get(applicant=each_student,company=employee) not in final_list:
                                                final_list.append(applyjob.objects.get(applicant=each_student,company=employee))
                        elif  object_list2 !=[]:
                            if ages==[]:
                                final_list=object_list2
                            else:
                                for age in ages:
                                    if age=="all":
                                        if applyjob.objects.get(applicant=each_student,company=employee) in object_list2: 
                                            if applyjob.objects.get(applicant=each_student,company=employee) not in final_list:
                                                final_list.append(applyjob.objects.get(applicant=each_student,company=employee))
                                    elif age=="21to25":
                                        if year >= 21 and year <= 25:
                                            if applyjob.objects.get(applicant=each_student,company=employee) in object_list2: 
                                                if applyjob.objects.get(applicant=each_student,company=employee) not in final_list:
                                                    final_list.append(applyjob.objects.get(applicant=each_student,company=employee))
                                    elif age=="26to30":
                                        if year >= 26 and year <= 30:
                                            if applyjob.objects.get(applicant=each_student,company=employee) in object_list2: 
                                                if applyjob.objects.get(applicant=each_student,company=employee) not in final_list:
                                                    final_list.append(applyjob.objects.get(applicant=each_student,company=employee))

        return render(request,"company_view_applicant.html",{'applies':final_list})
         
    return render(request,"company_view_applicant.html",{'applies':applies})

def search_result(request):
    name=""
    location=""
    if request.method=="POST":
        if 'login' in request.POST:
            request.session['email'] = request.POST['email']
            request.session['password'] = request.POST['password']
            return redirect('home')
        
        if 'search' in request.POST:
            name=request.POST['name']
            location=request.POST['location']
    else:
        name=request.session.get('name',None)
        location=request.session.get('location',None)

    object_list=[]
    if name == None:
        object_list=job.objects.all().order_by('-creation_date')
        
    else:
        title_list=job.objects.filter(title__icontains=name).order_by('-creation_date')
        skill_list=job.objects.filter(skills__icontains=name).order_by('-creation_date')
        time_list=job.objects.filter(time__icontains=name).order_by('-creation_date')
        company_list=job.objects.filter(company__name__icontains=name).order_by('-creation_date')
        for i in title_list:
            object_list.append(i)
        for i in skill_list:
            if i not in object_list:
                object_list.append(i)
        for i in time_list:
            if i not in object_list:
                object_list.append(i)
        for i in company_list:
            if i not in object_list:
                object_list.append(i)

    if location == None:
        loc=job.objects.all().order_by('-creation_date')
        location=""
    else:
        loc=job.objects.filter(location__icontains=location).order_by('-creation_date')
    final_list=[]
    for i in object_list:
        if i in loc:
            final_list.append(i)
    length=len(final_list)
    return render(request,'search_result.html',{'jobs':final_list,'name':name,'location':location,'len':length})

def job_detail(request,id):
    job_detail=job.objects.get(id=id)
    if request.method=="POST":
        if 'login' in request.POST:
            request.session['email'] = request.POST['email']
            request.session['password'] = request.POST['password']
            return redirect('home')
                    
        if 'search' in request.POST:
            request.session['name'] = request.POST['name']
            request.session['location'] = request.POST['location']
            return redirect('search_result')
    response=""
    parameters= {
        "key":"m2Zik9ujvwY9RlIOy7VWWYbaeR4fOPSg",
        "location":job_detail.location,
    }
    response =requests.get("https://www.mapquestapi.com/geocoding/v1/address",params=parameters)
    data= json.loads(response.text)['results']
    lat=data[0]['locations'][0]['latLng']['lat']
    lng=data[0]['locations'][0]['latLng']['lng']
    
    return render(request,"job_detail.html",{'job':job_detail,'latitude':lat,'longitude':lng})

def log_out(request):
    logout(request)
    return redirect('/')
    
def user_profile(request):
    if not request.user.is_authenticated:
        return redirect('home')
    
    User=student.objects.get(name=request.user)
    return render(request,'user_profile.html',{'user':User})

def edit_user_profile(request):
    if not request.user.is_authenticated:
        return redirect('home')

    User=student.objects.get(user=request.user)
    if request.method == "POST":
        if 'info-update' in request.POST:
            email=request.POST['email'] 
            phone=request.POST['phone']

            User.email=email
            User.phone=phone
            User.save()

            return redirect('user_profile')

        if 'file-update' in request.POST:
            resume = request.FILES['resume']

            User.resume=resume
            User.save()
            
            return redirect('user_profile')
    return render(request,'edit_user_profile.html',{'user':User})  

def user_search_result(request):
    if not request.user.is_authenticated:
        return redirect('home')
 
    if request.method=="POST":
        if 'search' in request.POST:
            name=request.POST['name']
            location=request.POST['location']
    else:
        name=request.session.get('name',None)
        location=request.session.get('location',None)
        
    count=0
    name=name
    location=location
    history=searchTerm.objects.filter(user=student.objects.get(name=request.user))
    for hist in history:
        if (name==hist.name and location==hist.location):
            count=count+1
            break
        else:
            count=0
    if(count!=1):
        searchitem=searchTerm.objects.create(user=student.objects.get(name=request.user),name=name,location=location)
        searchitem.save()
            
    object_list=[]
    if name == None:
        object_list=job.objects.all().order_by('-creation_date')
    else:
        title_list=job.objects.filter(title__icontains=name).order_by('-creation_date')
        skill_list=job.objects.filter(skills__icontains=name).order_by('-creation_date')
        time_list=job.objects.filter(time__icontains=name).order_by('-creation_date')
        company_list=job.objects.filter(company__name__icontains=name).order_by('-creation_date')
        for i in title_list:
            object_list.append(i)
        for i in skill_list:
            if i not in object_list:
                object_list.append(i)
        for i in time_list:
            if i not in object_list:
                object_list.append(i)
        for i in company_list:
            if i not in object_list:
                object_list.append(i)

    if location == None:
        loc=job.objects.all().order_by('-creation_date')
    else:
        loc=job.objects.filter(location__icontains=location).order_by('-creation_date')
    final_list=[]
    for i in object_list:
        if i in loc:
            final_list.append(i)
    length=len(final_list)
    return render(request,'user_search_result.html',{'jobs':final_list,'name':name,'location':location,'len':length})

def user_job_detail(request,id):
    if not request.user.is_authenticated:
        return redirect('home')

    job_detail=job.objects.get(id=id)
    user=student.objects.get(name=request.user)
    duplicate=applyjob.objects.filter(job=job_detail,applicant=user).first()
    if duplicate != None:
        unique=True
    else:
        unique=False
    if request.method=="POST":                   
        if 'search' in request.POST:
            request.session['name'] = request.POST['name']
            request.session['location'] = request.POST['location']
            return redirect('user_search_result')
        
        if 'apply' in request.POST:
            user=student.objects.get(name=request.user)
            specific_job= job.objects.get(id=id)
            applyjob.objects.create(company=specific_job.company,applicant=user,job=specific_job,resume=user.resume,apply_date=date.today())
            unique=True
    response=""
    parameters= {
        "key":"m2Zik9ujvwY9RlIOy7VWWYbaeR4fOPSg",
        "location":job_detail.location
    }
    response =requests.get("https://www.mapquestapi.com/geocoding/v1/address",params=parameters)
    data= json.loads(response.text)['results']
    lat=data[0]['locations'][0]['latLng']['lat']
    lng=data[0]['locations'][0]['latLng']['lng']
    
    return render(request,"user_job_detail.html",{'job':job_detail,'unique':unique,'latitude':lat,'longitude':lng})

def user_applied_list(request):
    if not request.user.is_authenticated:
        return redirect('home')

    applicant=student.objects.get(name=request.user)
    applies=applyjob.objects.filter(applicant=applicant)
    return render(request,"user_applied_list.html",{'applies':applies})

def user_homepage(request):
    if not request.user.is_authenticated:
        return redirect('home')
    
    count=0
    applicant=student.objects.get(name=request.user)
    words=""
    pdf=fitz.open("../fyp1"+applicant.resume.url)
    for text in pdf:
        words+=text.get_text()
    words=regex.sub(r'\d+',' ',words)
    words=regex.sub('httpS+s*',' ',words)
    words=words.strip()
        
    term ={
        'ICT User Support Technicians':['troubleshooting', 'mandarin', 'english', 'bahasa malaysia', 'cisco', 'sql', 'debugging', 'itil', 'problem solving', 'javascript', 'java', 'c', 'failure analysis', 'hardware troubleshooting', 'oracle', 'vmware', 'software installation' ,'computer troubleshooting', 'hardware and software installation', 'jquery', 'mysql', 'network administration', 'network troubleshooting', 'pc support', 'server configuration', 'cloud computing', 'computer troubleshooting', 'software installation', 'crisis management', 'indonesian', 'equipment maintenance', 'microsoft exchange server', 'network management'],

        'ICT Installers and Services':['animation', 'bahasa malaysia', 'audio editing', 'cabling', 'english', 'multisim', 'mandarin', 'wiring', 'network administration'],

        'ICT Managers':['english', 'communication', 'leadership', 'project management', 'planning', 'problem solving', 'mandarin', 'bahasa malaysia', 'digital marketing', 'project planning', 'itil', 'risk assessment', 'critical thinking', 'it management', 'decision making', 'machine learning', 'team management', 'configuration management', 'vendor management', 'crisis management', 'oracle transportation management', 'program management', 'process management', 'sales planning', 'strategic communications', 'supplier management', 'strategic management'],

        'IT Trainers':['.net', 'communication', 'bahasa malaysia', 'english', 'javascript', 'writing', 'programming', 'listening','public speaking', 'time management', 'python', 'ruby', 'troubleshooting', 'writing'],
        
        'ICT Sales Professionals':['english', 'communication', 'mandarin', 'planning', 'digital marketing', 'bahasa malaysia', 'analysis', 'research', 'analytics', 'problem solving', 'writing', 'written communication', 'project management', 'leadership', 'korean', 'japanese', 'listening', 'active listening', 'order management', 'attribution modeling', 'channel marketing', 'business management', 'order processing', 'purchasing', 'product marketing', 'leadership', 'cost analysis', 'product management', 'forecasting', 'costing', 'administration management', 'online advertising', 'sales analysis', 'digital advertising', 'invoicing', 'system integration testing', 'social media marketing', 'business analysis', 'contract negotiation', 'german', 'public speaking', 'website management', 'decision making', 'critical thinking', 'internet marketing', 'operations management', 'business planning', 'process management', '.net'],
        
        'ICT Operation Technicians':['english', 'bahasa malaysia', 'troubleshooting', 'communication', 'mandarin', 'programming', 'sql', 'c', 'ajax', 'asp.net', 'c#', 'c++', 'os x', 'hyper-v', 'javascript', 'pc installation', 'root cause analysis', 'software installation', 'scada', 'vmware', 'web programming', 'xhtml', 'electrical writing', 'mysql', 'computer literacy', 'computer maintenance', 'equipment maintenance', 'equipment installation', 'equipment repair', 'debugging', 'network administration', 'report writing', 'problem analysis', 'system integration testing', 'warehouse management', 'wiring', 'microsoft office'],
        
        'System Analysts':['english', 'communication', 'analysis', 'troubleshooting', 'sql', 'planning', 'project management', 'java', 'problem solving', 'writing', 'mandarin', 'speaking', 'oracle', 'system design', 'javascript', 'bahasa malaysia', 'itil', 'c#', 'leadership', 'analytics', 'data migration', 'time management', 'research', 'written communication', 'mysql', 'debugging', '.net', 'japanese', 'css', 'asp.net', 'python', 'c++', 'requirements analysis', 'root cause analysis', 'business analysis', 'warehouse management', 'database design', 'data management', 'decision making', 'listening', 'microsoft sql', 'korean', 'quality management', 'critical thinking', 'data analysis', 'resource planning', 'prototyping', 'microsoft sharepoint'],
        
        'Software Developers':['programming', 'javascript', 'java', 'english', 'c#', 'communication', 'sql', '.net', 'analysis', 'css', 'mysql', 'troubleshooting', 'debugging', 'mandarin', 'c++', 'writing', 'python', 'oracle', 'problem solving', 'research', 'planning', 'jquery', 'asp.net', 'leadership', 'html5', 'laravel', 'bahasa malaysia', 'bootstrap', 'mongodb', 'project management', 'node.js', 'speaking', 'postgresql', 'system design', 'object-oriented programming', 'microsoft sql', 'ajax', 'time management', 'autocad', 'analytics', 'database design', 'visual studio', 'angular js', 'nosql', 'microsoft office', 'xcode', 'vmware', 'critical thinking'],
        
        'Web and Multimedia Developers':['javascript', 'mysql', 'css', 'java', 'english', 'programming', 'html5', 'jquery', 'bootstrap', 'writing', 'communication', 'debugging', 'writing', 'mandarin', 'sql', 'laravel', 'research', 'c#', '.net', 'node.js', 'bootstrap', 'HTML', 'programming', 'planning', 'python', 'ajax', 'asp.net', 'problem solving', 'leadership', 'mongodb', 'troubleshooting', 'bahasa malaysia', 'postgresql', 'time management', 'angular js', 'web design', 'graphic design', 'animation', 'photoshop', 'django', 'microsoft sql', 'adobe illustrator', 'visual studio', 'illustrator', 'cloud computing', 'web analytics', 'web programming' 'visual design', 'adobe photoshop', 'indesign', 'drupal', 'jquery mobile'],
        
        'Software and Applications Developers and Analysts Not Elsewhere Classified':['english', 'communication', 'analysis', 'leadership', 'software testing', 'quality management', 'writing', 'troubleshooting', 'debugging', 'regression testing', 'mandarin', '.net', 'performance testing',  'bahasa malaysia','performanace management', 'product testing', 'root cause analysis', 'risk assessment', 'ajax', 'failure analysis', 'teststand', 'japanese', 'korean', 'listening', 'laravel', 'server configuration', 'system integration testing',  'testng','administration management', 'API management','capacity management', 'black-box testing', 'audit planning', 'data validataion', 'information assurance','embedded systems', 'java se', 'objective c', 'performance management', 'penetration testing', 'process testing', 'product demonstration', 'reliability analysis', 'public speaking', 'risk based testing', 'security testing', 'software validation' 'rules engines', 'security testing'],
        
        'Database Designers and Administrators':[ 'sql', 'english', 'oracle', 'troubleshooting', 'planning', 'database design', 'mysql', 'mandarin', 'communication', 'analysis', 'database administration', 'database architecture', 'postgresql', 'microsoft sql', 'capacity planning', 'problem solving', 'research', 'data migration', 'data warehousing', 'database management', 'leadership', 'writing', 'mongodb', 'bahasa malaysia', 'data management', 'database maintenance', 'analytics', 'database management systems', 'performance analysis', 'data modeling', 'asp.net', 'db2', 'mariadb', 'oracle golden gate', 'nosql', 'system design', '.net', 'creative problem solving', 'administration management', 'critical thinking', 'data acquisition', 'data archiving', 'data analysis', 'data conversion', 'data engineering', 'data manipulation', 'data integration', 'data mining'],
        
        'Systems Administrators':['english', 'communication', 'troubleshooting', 'mandarin', 'analysis', 'planning', 'bahasa malaysia', 'problem solving', 'programming', 'leadership', 'project management', 'system administration', 'writing', 'japanese', 'cloud computing', 'debugging', 'system design', '.net', 'root cause analysis', 'network administration', 'microsoft active directory', 'vulnerability assessment', 'database administration', 'administration management', 'IT managament', 'oracle cloud', 'microsoft sharepoint', 'sap security', 'visual c++', 'cassandra', 'korean', 'cloud architecture', 'remote technical support', 'warehouse management', 'sql server reporting services', 'ssrs', 'adobe creative cloud', 'cloud security infrastructure', 'ibm db2', 'file management', 'kerberos', 'linux kernel', 'malware analysis', 'listening', 'microsoft sccm', 'password management', 'MYSQL database administration', 'password management', 'operations management', 'sap technical architecture'],
        
        'Computer Network Professionals':['troubleshooting', 'english', 'cisco', 'communication', 'planning', 'mandarin', 'bahasa malaysia', 'analysis', 'network administration', 'network management', 'writing', 'performance management', 'network planning', 'ajax', 'networking troubleshooting', 'API managament', 'intrusion detection', 'jquery', 'japanese', 'silver peak', 'c++', 'leadership', 'debugging', 'netscreen', 'network installation', 'asp.net', 'node.js', 'autoit', 'database management', 'cisco routing', 'cisco switching', 'LAN administration', 'microsoft sharepoint', 'malware analysis', 'network analytics', 'listening', 'scada', 'software maintenance', 'security information and event management', 'traffic analysis'],
        
        'Data Professionals':['analysis', 'analytics', 'sql', 'english', 'python', 'communication', 'data management', 'planning', 'data analysis', 'leadership', 'research', 'machine learning', 'mandarin', 'troubleshooting', 'writing', 'problem solving', 'business analysis', 'bahasa malaysia', 'data mining', 'data visualization', 'decision making', 'sas', 'data engineering', 'data warehousing', 'forecasting', 'data acquisition', '.net', 'data modeling', 'statistical analysis', 'japanese', 'data cleaning', 'data integration', 'predictive models', 'database management', 'data validation', 'listening', 'data mapping', 'data entry', 'database administration', 'korean', 'big data analytics', 'mathematical programming', 'data manipulation', 'data migration', 'data visualisation', 'data transformation', 'k-means'],
        
        'Cybersecurity Professionals':['english', 'troubleshooting', 'communication', 'analysis', 'penetration testing', 'mandarin', 'leadership', 'problem solving', 'research', '.net', 'planning', 'risk assessment', 'vulnerability assessment', 'javascript', 'writing', 'security testing', 'root cause analysis', 'itil', 'intrusion detection', 'bahasa malaysia', 'selenium', 'security incident management', 'malware analysis', 'threat hunting', 'listening', 'system administration', 'security design', 'administration management', 'crisis management', 'decision making, performance management', 'performance testing', 'phishing', 'security assessments', 'wireless security', 'sap security', 'backup administration', 'arcgis', 'computer network defense', 'cloud security architecture', 'conflict management', 'database administration', 'cybersecurity assessment', 'database management', 'disaster recovery planning', 'information assurance', 'imperva securesphere',  'iaas security'],
        
        'Animation and Visual Effects Professionals':['english', 'editing', 'research', 'writing', 'mandarin', 'adobe photoshop', 'communication', 'bahasa malaysia', 'photoshop', 'illustrator', 'graphic design', 'planning', 'animation', 'adobe illustrator', 'video editing', 'time management', 'illustration', 'motion graphics', 'autocad', 'motion graphics', '3d studio max', 'problem solving', 'leadership', 'videography', '3d modeling', '3d rendering', 'project management', 'adobe acrobat', 'sketchup', 'japanese', 'listening', 'adobe indesign', 'video production', 'photo editing', 'visual design', 'v-ray', 'storyboarding', 'image editing', '2d animation', 'desktop publishing', 'adobe premiere', '3d rendering', 'adobe audition', 'critical thinking', 'character design', 'indesign', 'korean', 'adobe creative cloud', '3d visualization', 'adobe flash', '3d visualization'],   
        
        'Digital Games and eSPORTS Professionals':['adobe photoshop', 'english', 'animation', 'illustrator', 'leadership', 'adobe illustrator', 'photoshop', 'communication', 'editing', 'writing', 'illustration', 'autocad', 'mandarin', 'time management', 'motion graphics', 'analysis', 'planning', 'project management', 'problen solving', 'v-ray', 'autodesk maya', 'graphic design', 'creative design', 'indesign', 'mobile games', 'video production', 'research', '2D animation', '3D modeling', 'adobe audition', 'adobe indesign', 'adobe creative cloud', 'bahasa malaysia', 'computer animation', 'interaction design', 'digital marketing', 'japanese', 'performance management', 'listening', 'prototyping', 'schematic design', 'sketchup', 'social media marketing', 'system administration', 'team management', 'video editing', 'user interface design', 'video streaming'],
        
        'Creative Content Designers Professionals':['graphic design', 'photoshop', 'english', 'illustrator', 'mandarin', 'adobe photoshop', 'adobe illustrator', 'bahasa malaysia', 'communication', 'video editing', 'time management', 'research', 'planning', 'editing', 'writing', 'planning', 'indesign', 'animation', 'web design', 'videography', 'css', 'digital marketing', 'autocad', 'visual design', 'motion graphics', 'javascript', 'creative design', 'illustration', 'adobe acrobat', 'adobe indesign', 'copywriting', 'leadership', 'video production', 'project management', 'digital design', 'adobe premiere', 'desktop publishing', 'photo editing', 'jquery', 'html5', 'sketchup', 'sketching', 'troubleshooting', 'storyboarding', 'digital advertising', 'image editing', 'content marketing', 'bootstrap', 'design thinking'],
        
        'Computer Network and Systems Technicians':['troubleshooting', 'english', 'cisco', 'mandarin', 'network administration', 'cable pulling', 'bahasa malaysia', 'cloud computing', 'itil', 'local area network', 'lan', 'penetration testing', 'programming', 'sytem administration', 'security testing', 'wide area network', 'wan'],
        
        'Applications Programmers':['programming', 'english', 'javascript', 'sql', 'c#', 'mysql', 'css', 'communication', 'writing', 'java', 'asp.net', 'mandarin', 'troubleshooting', 'jquery', 'debugging', 'problem solving', '.net', 'laravel', 'problem solving', 'oracle', 'problem solving', 'bahasa malaysia', 'bootstrap', 'ajax', 'c++', 'html5', 'planning', 'leadership', 'angularjs', 'microsoft sql', 'mongodb', 'written communication', 'postgresql', 'project management', 'cobol', 'node.js', 'python', 'written communication', 'database design', 'mongodb', 'postgresql', 'project management', 'python', 'cobol', 'node.js', 'database design', 'python', 'software testing', 'creative problem solving','system design', 'interface design', 'junit', 'nosql', 'mariadb', 'ruby', 'software support', 'system integration testing' 'tomcat', 'xhtml'],
    }
    
    user_support_technicians=0
    installers_and_services=0
    managers=0
    trainers=0
    sales=0
    operation_technicians=0
    system_analyst=0
    software_developers=0
    web_and_multimedia_developers=0
    software_and_applications_developers_and_analysts=0
    database_designers_and_administrators=0
    system_administrators=0
    computer_network=0
    data=0
    cybersecurity=0
    animation_and_visual_effects=0
    digital_games_and_eSports=0
    creative_content_designers=0
    computer_network_and_systems_technicians=0
    application_programmers=0
    score=[]

    for area in term.keys():
        if area == 'ICT User Support Technicians':
            for word in term[area]:
                if word in words:
                    user_support_technicians +=1

        elif area == 'ICT Installers and Services':
            for word in term[area]:
                if word in words:
                    installers_and_services +=1

        elif area == 'ICT Managers':
            for word in term[area]:
                if word in words:
                    managers +=1
            
        elif area == 'IT Trainers':
            for word in term[area]:
                if word in words:
                    trainers +=1

        elif area == 'ICT Sales Professionals':
            for word in term[area]:
                if word in words:
                    sales +=1

        elif area == 'ICT Operation Technicians':
            for word in term[area]:
                if word in words:
                    operation_technicians +=1

        elif area == 'System Analysts':
            for word in term[area]:
                if word in words:
                    system_analyst +=1
            

        elif area == 'Software Developers':
            for word in term[area]:
                if word in words:
                    software_developers +=1

        elif area == 'Web and Multimedia Developers':
            for word in term[area]:
                if word in words:
                    web_and_multimedia_developers +=1

        elif area == 'Software and Applications Developers and Analysts Not Elsewhere Classified':
            for word in term[area]:
                if word in words:
                    software_and_applications_developers_and_analysts +=1

        elif area == 'Database Designers and Administrators':
            for word in term[area]:
                if word in words:
                    database_designers_and_administrators +=1
 
        elif area == 'Systems Administrators':
            for word in term[area]:
                if word in words:
                    system_administrators +=1 
            
        elif area == 'Computer Network Professionals':
            for word in term[area]:
                if word in words:
                    computer_network +=1
            
        elif area == 'Data Professionals':
            for word in term[area]:
                if word in words:
                    data +=1
            
        elif area == 'Cybersecurity Professionals':
            for word in term[area]:
                if word in words:
                    cybersecurity +=1  
            
        elif area == 'Animation and Visual Effects Professionals':
            for word in term[area]:
                if word in words:
                    animation_and_visual_effects +=1
            
        elif area == 'Digital Games and eSPORTS Professionals':
            for word in term[area]:
                if word in words:
                    digital_games_and_eSports +=1
        
        elif area == 'Creative Content Designers Professionals':
            for word in term[area]:
                if word in words:
                    creative_content_designers +=1
            
        elif area == 'Computer Network and Systems Technicians':
            for word in term[area]:
                if word in words:
                    computer_network_and_systems_technicians +=1
            
        elif area == 'Applications Programmers':
            for word in term[area]:
                if word in words:
                    application_programmers +=1
        
    if CareerTest.objects.filter(user=applicant).exists():
        if CareerTest.objects.filter(user=applicant).first().q1 == 'yes':
            computer_network_and_systems_technicians +=1
            computer_network +=1
            cybersecurity +=1                                             
           
        if CareerTest.objects.filter(user=applicant).first().q2 == 'yes':
            software_developers +=1
            software_and_applications_developers_and_analysts +=1
            application_programmers +=1
            web_and_multimedia_developers +=1
            creative_content_designers +=1
            animation_and_visual_effects +=1
            digital_games_and_eSports +=1
           
        if CareerTest.objects.filter(user=applicant).first().q3 == 'yes':
            computer_network_and_systems_technicians +=1
            computer_network +=1
            cybersecurity +=1
        
        if CareerTest.objects.filter(user=applicant).first().q4 == 'yes':
            installers_and_services +=1
              
        if CareerTest.objects.filter(user=applicant).first().q5 == 'yes':
            web_and_multimedia_developers +=1
            creative_content_designers +=1
            animation_and_visual_effects +=1
            digital_games_and_eSports +=1
           
        if CareerTest.objects.filter(user=applicant).first().q6 == 'yes':
            computer_network_and_systems_technicians +=1
            computer_network +=1
            cybersecurity +=1
        
        if CareerTest.objects.filter(user=applicant).first().q7 == 'yes':
            web_and_multimedia_developers +=1
            creative_content_designers +=1
            animation_and_visual_effects +=1
            digital_games_and_eSports +=1
            software_developers +=1
            software_and_applications_developers_and_analysts +=1
            application_programmers +=1
           
        if CareerTest.objects.filter(user=applicant).first().q8 == 'yes':
            software_developers +=1
            software_and_applications_developers_and_analysts +=1
            application_programmers +=1
            operation_technicians +=1
           
        if CareerTest.objects.filter(user=applicant).first().q9 == 'yes':
            installers_and_services +=1
            user_support_technicians +=1
        
        if CareerTest.objects.filter(user=applicant).first().q10 == 'yes':
            software_developers +=1
            software_and_applications_developers_and_analysts +=1
            application_programmers +=1
        
        if CareerTest.objects.filter(user=applicant).first().q11 == 'yes':
            database_designers_and_administrators +=1
            data +=1
            system_analyst +=1
            system_administrators +=1
                
        if CareerTest.objects.filter(user=applicant).first().q12 == 'yes':
            computer_network_and_systems_technicians +=1
            computer_network +=1
            cybersecurity +=1              

        if CareerTest.objects.filter(user=applicant).first().q13 == 'yes':
            computer_network_and_systems_technicians +=1
            computer_network +=1
            cybersecurity +=1
            database_designers_and_administrators +=1
            data +=1
            system_analyst +=1
            system_administrators +=1
        
        if CareerTest.objects.filter(user=applicant).first().q14 == 'yes':
            software_developers +=1
            software_and_applications_developers_and_analysts +=1
            application_programmers +=1
            user_support_technicians +=1
            operation_technicians +=1
            database_designers_and_administrators +=1
            data +=1
            
        if CareerTest.objects.filter(user=applicant).first().q15 == 'yes':
            software_developers +=1
            software_and_applications_developers_and_analysts +=1
            application_programmers +=1
            web_and_multimedia_developers +=1
            creative_content_designers +=1
            animation_and_visual_effects +=1
            digital_games_and_eSports +=1  
        
        if CareerTest.objects.filter(user=applicant).first().q16 == 'yes':
            sales +=1
            user_support_technicians +=1

        if CareerTest.objects.filter(user=applicant).first().q17 == 'yes':
            sales +=1
            user_support_technicians +=1
           
        if CareerTest.objects.filter(user=applicant).first().q18 == 'yes':
            operation_technicians +=1
            installers_and_services +=1
        
        if CareerTest.objects.filter(user=applicant).first().q19 == 'yes':
            user_support_technicians +=1
            installers_and_services +=1
        
        if CareerTest.objects.filter(user=applicant).first().q20 == 'yes':
            user_support_technicians +=1
            installers_and_services +=1
            trainers +=1     
    
    score.append(application_programmers)
    score.append(computer_network_and_systems_technicians)
    score.append(creative_content_designers)
    score.append(digital_games_and_eSports)
    score.append(animation_and_visual_effects)
    score.append(cybersecurity)
    score.append(data)
    score.append(system_administrators)
    score.append(computer_network)
    score.append(database_designers_and_administrators)
    score.append(software_and_applications_developers_and_analysts)
    score.append(web_and_multimedia_developers)
    score.append(software_developers)
    score.append(system_analyst)
    score.append(operation_technicians)   
    score.append(sales)  
    score.append(trainers) 
    score.append(managers)
    score.append(installers_and_services)
    score.append(user_support_technicians)    
           
    summary = pd.DataFrame(score,index=term.keys(),columns=['score']).sort_values(by='score',ascending=False)
    keywords=summary.iloc[0].name
    history=searchTerm.objects.filter(user=student.objects.get(name=request.user))
    for hist in history:
        if (hist.name!=""):
            hist_name=hist.name.split(" ")
            term[keywords].extend(hist_name)
            
        if (hist.location!=""):
            hist_loca=hist.location.split(" ")
            term[keywords].extend(hist_loca)
                   
    jobs ={
        'ICT User Support Technicians':['Computer Help Desk Technician', 'Personal Computer Support Technician', 'Information Technology Technician', 'Computer Help Desk Operator', 'Communication and Computer Engineering Assistant', 'Computer Assistant', 'Communications Assistant', 'Database Assistant', 'Computer Programming Assistant', 'Computer User Services Assistant', 'Customer Help Desk Officer', 'Call Centre Trainer', 'Data Centre Supervisor', 'Data Centre Assistant', 'Technicial Support Technician', 'Wireless Operator', 'Technical Assistant', 'Accounting Software Support Technician', 'Failure Analysis Technician'],
        
        'ICT Installers and Services':['Telephone Wireman', 'Telephone and Telegraph Installer', 'Telephone and Telegraph Mechanic', 'Telephone and Telegraph Servicer', 'Information Technology Support Worker', 'Data and Telecommunications Cabler', 'Computer Equipment Fitter', 'Fitter, Electronics Radio Television Equipment', 'Fitter, Electronics Video and Radar Equipment', 'Fitter, Electronics Radar Equipment', 'Fitter, Electronics Computer', 'Operator, Network', 'Operator, Wireless Equipment', 'Computer Operator'],
        
        'ICT Managers':['Chief Information Officer', 'Chief Data Officer', 'Chief Information Security Officer', 'Chief Information Technology Officer', 'Chief Information Technology Architect', 'Information Systems Manager', 'Information Technology Manager', 'Village Community Center Manager', 'Production and Operation Manager, Communications', 'Computer Services Manager', 'Data Processing Manager', 'Application Development Manager', 'Data Operations Manager', 'ICT Development Manager', 'Information Systems Director', 'Internet Service Provider', 'Network Manager', 'Animation Director', 'Audio Visual Manager', 'Database Manager', 'Computer Security Manager', 'Information Technology Project Manager', 'Information Technology Infrastructure Manager', 'Information Technology Programme Manager', 'Information Technology Sales Manager', 'Information Technology Resource Manager', 'Bioinformatics Manager', 'Creative Multimedia Manager', 'Network Performance Manager', 'Network Operations Manager', 'Network Deployment Manager', 'Information Technology Business Development Manager', 'Technology Transformation Manager', 'Information Technology Support Manager', 'Software Development Manager', 'E-Commerce Application Development Manager', 'Information Technology Governance Manager', 'Building Information Modelling Manager', 'Risk Manager', 'Director of Cybersecurity', 'Security Operation Manager', 'Solution Architect Manager', 'Software Architect Manager', 'Data Analytics Manager', 'Failure Analysis Section Head'],
        
        'IT Trainers':['Satellite-Instruction Facilitator', 'Computer Trainer', 'Software Trainer'],
        
        'ICT Sales Professionals':['Sales Representative, Information and Communications Technology', 'Sales Representative, Computer', 'Product Support Engineer', 'Information Technology Sales Engineer', 'Customer Support Representative', 'Information Technology Product Engineer', 'Product Support Officer', 'Sales Application Engineer', 'Product Development Engineer', 'Digital Banking/Internet Technology Specialist', 'Customer Support Officer ', 'Customer Support Engineer', 'E-Commerce Executive'],
        
        'ICT Operation Technicians':['Computer Technician', 'Administrative Assistant', 'Administrative Assistant', 'Executive Assistant', 'Computer Technician', 'Computer Peripheral Equipment Technician', 'Computer Peripheral Equipment Console Technician', 'Computer Peripheral Equipment High-Speed Printer Technician', 'Electronic Data Processing Technician', 'Computer Engineering Assistant', 'Assistant Supervisor, Electronic Data Processing', 'Electronic Data Processing Supervisor', 'Semi-Conductor Technician', 'Information Systems Technician', 'Information Technology Assistant', 'Computer Console Operator', 'Systems Operator', 'Computer Operator', 'High-Speed Computer Printer Operator', 'Computer Peripheral Equipment Operator', 'Hardware Technician', 'Administrative Assistant, Computer Technician', 'Engineering Assistant, Telecommunications', 'Supervisor, Management Information Systems', 'Assistant Information Technology Officer Grade FA29', 'Assistant Executive Officer', 'Assistant Executive Officer', 'Assistant Executive Officer', 'Assistant Information Technology Officer', 'Assistant Computer System Executive', 'Service Technician', 'Assistant Computer Systems Analyst', 'Computer Systems Analysis Assistant', 'Computer Programmer', 'PLC Assistant Engineer'],
        
        'System Analysts':['Management Information Systems Analyst', 'Computer Systems Analyst', 'Computer Consultant', 'Information Technology Systems Consultant', 'Information Technology Consultant', 'Information Technology Business Analyst', 'Information Technology Researcher', 'Information Technology Researcher', 'Information Technology Systems Designer', 'Information Technology Systems Designer', 'RPG System Analyst', '.Net Consultant', '.Net Application Consultant', 'Information Technology Consultant', 'Information Technology Specialist', 'Information Technology Specialist', '5Information Technology Specialist', 'Java Application Consultant', 'Information Technology Consultant', 'Information Technology Specialist', 'Technical Specialist', 'Information Technology System Analyst', 'JD Edwards Application Specialist', 'Information Technology Specialist', 'Application Specialist Support', 'Application Specialist Support', 'Application Specialist Support', 'Application Specialist Support', 'Application Specialist Support', 'Application Specialist Support', 'Peoplesoft Financials Functional Consultant', 'Peoplesoft Financials Functional Consultant', 'Enterprise Resource Planning Technical Specialist', 'Information Technology Specialist SAP', 'Sharepoint Consultant', 'Sharepoint Technical Specialis', 'Sharepoint Specialist', 'Siebel Specialist', 'Information Technology Application Management Analyst', 'Information Technology Specialist', 'Siebel Customer Relationship Management Consultant', 'Register Transfer Level Designer', 'Analog Integrated Circuit Designer ', 'Design Engineer', 'Integrated Circuit Designer', 'Logic Designer', 'Mixed Signal Integrated Circuit Designer ', 'Power Integrated Circuit Designer', 'Radio Frequency Integrated Circuit Design Engineer', 'Technical Helpdesk Analyst', 'Computer Systems Integrated Analyst', 'JD-Edwards Consultant', 'SAP Consultant', 'System Analysis Engineer', 'Information and Communication Technology Specialist', 'Navision Functional Consultant', 'E-Commerce System Analyst', 'CAE Engineer', 'Information Technology Specialist', 'System Analyst', 'Technology Innovation Analyst', 'Digital Analyst', 'Digital Transformation Executive/Officer', 'Derivative Processing Analyst', 'System Analyst', 'System Application and Products Business Analyst', 'Service Desk Specialist', 'Requirements Analyst', 'Search Engine Advertising Analyst', 'Service Desk Analyst', 'Vendor Management Analyst', 'System Application and Products Consultant', 'System Application and Product Test Analyst'],
        
        'Software Developers':['Software Developer', 'Multimedia Software Developer (.NET)', 'Software Designer', 'Design Engineer', '.Net Developer', 'Application Developer', 'Application Engineer', 'Software Engineer', 'C/C++ Developer', 'C/C++ Software Engineer', 'Cobol Developer', 'Microfocus Cobol Developer', 'Java Application Developer', 'Java Developer', 'Hypertext Preprocessor Developer', 'Hypertext Preprocessor Web Programmer ', 'Information Technology Role-Playing Game Executive ', 'Lotus Notes Developer', 'Information Technology System Architect', 'Information Technology Technical Architect', 'Navision Developer', 'Net Sharepoint Developer', 'Software Engineer ', 'Siebel Developer', 'Software Analyst', 'Software Design Engineers', 'Root Cause Failure Analysis Engineer', 'Systems Applications and Products and Finance IT Developer', 'Systems Applications and Products Developer ', 'OpenText Developer', 'Data Visualization Developer', 'Debug Software Engineer', 'Computer Engineer, Software', 'iOS Developer', 'Android Developer', 'Mobile Application Developer', 'System Application Engineer', 'Blockchain Developer', 'Linux Software Engineer', 'Programmable Logic Controller Engineer ', 'System Engineer', 'System Engineer', 'Information System Executive', 'Computer System Executive', 'Computer Systems Engineer', 'Management Information Systems Engineer', 'System Developer', 'System Engineer', 'Software Engineer  (Python)', 'Automated Guided Vehicle Software Engineer ', 'Oracle Developer', 'Cloud Developer', 'Javascript Developer', 'Angular Developer', 'Software Consultant', 'Application Developer', 'SQL Developer', 'Application Architect', 'Back-end Developer', 'Flutter Developer', 'API Developer', 'Ruby and Rails Developer', 'Machine Learning Developer ', 'Salesforce Developer', 'Business Intelligence Developer', 'Manufacturing Execution System Developer', 'Firmware Engineer', 'Firmware Engineer'],
        
        'Web and Multimedia Developers':['Website Developer', 'Internet / Intranet Developer', 'Website Architect', 'Webmaster', 'Website Administrator', 'UI/UX Front-end Developer', 'Full Stack Developer', 'E-Commerce Website Developer', 'Front-End Developer', 'Web and Mobility Developer', 'User Experience Engineer', 'Web Application Developer', 'Social Media Designer', 'Website Technician', 'Web Technician', 'Multimedia Animation', 'Assistant Graphic Designer', 'Art and Design Technician', 'Creative Assistance'],
        
        'Software and Applications Developers and Analysts Not Elsewhere Classified':['Software Tester', 'Systems Tester', 'Product Quality Assurance Engineer', 'Quality Assurance Analyst', 'Quality Assurance Executive', 'Quality Engineer', 'Test Engineer', 'Solution Architect', 'Application Assurance Engineer', 'Application Security Engineer', 'Software Quality Assurance Engineer', 'Siebel Solution Architect', 'Siebel Technical Architect', 'Application Consultant', 'Internal Auditor', 'Information Technology Auditor', 'E-Commerce System Test Engineer', 'Tester', '.Net Developer'],
        
        'Database Designers and Administrators':['Database Architect', 'Database Analyst', 'Database Administrator', 'Database Designer', 'Computer Auditor', 'Administrator, EDP', 'Oracle Database Engineer', 'Oracle Database Specialist', 'SQL Database Administrator', 'SQL Database Engineer', 'SQL Database Specialist', 'Data Warehouse Specialist', 'Database Specialist', 'Business Database Analysts', 'Hadoop Engineer', 'E-Commerce Database Administrator', 'E-Commerce Database Administrator', 'Data Centre Specialist', 'Data Centre Analyst', 'Database Engineer', 'SQL Database Developer ', 'Oracle Database Administrator', 'Data Centre Executive', 'SQL Database Developer'],
        
        'Systems Administrators':['Information Technology Officer', 'Executive Officer', 'Executive Officer', 'Executive Officer', 'Information System Officer', 'Network Communications Executive', 'Information Communications System Officer', 'Information Technology Support Officer', 'Systems Administrator', 'Computer System Administrator', 'Information Technology Executive', 'Information Technology Project Coordinator', 'Information Technology Project Administrator', 'Computer Support Engineer', 'Information Technology Technical Specialist', 'SAP Application Administrator', 'Access Administration Analyst', 'Inbound Technical Support Representative', 'NetApps Administrator', 'System Support Specialist', 'Information Systems Maintenance Engineer', 'Cloud Computing Solution Architect', 'Billing Specialist', 'Information Technology Architect', 'Enterprise Applications Architect', 'Cloud Technology Specialist', 'Cloud Planner', 'Technical Support Engineer', 'Integration Technology Specialist', 'Management Information System Specialist', 'Information Technology Infrastructure Specialists', 'Information Scientist, Technical Information', 'Information Scientist, Business Services', 'Information Technology Engineer', 'Systems Design Engineer', 'Technical System Administrator', 'BIM Coordinator', 'Geographic Information Systems Officer', 'Oracle Applications Administrator', 'Computer and System Administrator', 'Application Specialist', 'Delivery Consultant', 'Application Consultant', 'Cloud Architect', 'Salesforce Dot Com Specialist', 'Model Optimization Specialist', 'Service Support Engineer'],
        
        'Computer Network Professionals':['Network Analyst', 'Network Services Consultant', 'Network Administrator', 'Network Infrastructure Administrator', 'Network Engineer', 'Network Systems Engineer', 'Cloud Specialist', 'Radio Network Planning Consultant', 'Network Performance Consultant', 'Network System Engineer', 'Network Specialist', 'Network Performance', 'Communications Computer Analyst', 'Network Security Executive', 'Network Security Software Developers', 'Internet Protocol logic Design Engineer'],
        
        'Data Professionals':['Data Scientist', 'Big Data Engineer', 'Data Analyst', 'Data Modeller', 'Data Miner', 'Data Architect', 'Tera Data Analyst', 'Data Predictive Analyst', 'Data Mining Analyst', 'Big Data Analyst', 'Machine Learning Engineer', 'Deep Learning Engineer', 'Artificial Intelligence Engineer', 'Data Steward', 'E-Commerce Data Analyst', 'Business Data Analyst', 'Expert Big Data Analyst', 'Extract Transform Load Developer', 'Electronic Data Processing Analyst', 'Oracle Database Analyst', 'SQL Database Analyst', 'Data Conversion Specialist', 'Metadata Coordinator', 'Data Governance Migration Specialist', 'Digital Data  Reviewer', 'Data Migration Specialist'],
        
        'Cybersecurity Professionals':['Information and Communication Technology Security Executive', 'Cybersecurity Executive', 'Digital Forensic Specialist', 'Security Specialist', 'Security Technologist Specialist', 'Security Architect', 'Application Security Specialist', 'Security Strategist', 'Network Penetration Tester', 'Network Strategist', 'Technology Strategist', 'Enterprise Convergence Strategist', 'Access Control Specialist', 'Data Security Specialist', 'Security Engineer', 'Cybersecurity Architect', 'Cybersecurity Specialist', 'Information Security Analyst', 'Security Administrator', 'Information Security Officer', 'Incident Responder', 'Penetration Tester', 'Malware Analyst', 'Cyber Threat Investigator', 'Forensic Analyst', 'Cybersecurity Consultant', 'Cybersecurity Engineer', 'Systems Security Engineer', 'DevOps Engineer', 'Cybersecurity Analyst', 'Test Analyst', 'Security Officer', 'Security Executive', 'Cyber Risk Analyst', 'Security Penetration Tester', 'Security Infrastructure Engineer', 'Forensic Investigator', 'Principal Security Engineer', 'Internet Safety Evaluater', 'Information Technology Security Analyst', 'Information Security Consultant', 'Security Consultant'],
        
        'Animation and Visual Effects Professionals':['Layout Artist', '3D animator', '2D Animator', 'CG Modeler', '3D Modeller', 'Match Move Artist/3D Tracker', 'Lighting Artist', 'Render Wrangler', 'Roto Artist', 'Compositor/Composite Artist', 'Storyboard Artist', 'Scriptwriter / Screenwriter', 'Effects/FX Artist', 'Graphic Artist', 'Designer Artist', 'Digital Artist', 'Illustrator', 'Visualizer', 'Desktop Publishing Artist', 'Multimedia Artist', 'Graphics Illustrator', 'Technical Illustrator', 'Flash Animator', 'Flash Developer', 'Web Animator', 'Visualization Specialist', 'Computer Specialist', 'Story Content Writer', '3D Designer', 'Content Writer/Creator', '3D Generalist', 'Content Developer', 'Content Analyst', 'Content Moderator', 'Digital Content Writer/Creator'],
        
        'Digital Games and eSPORTS Professionals':['Game Designer', 'Level Designer ', 'QA Tester/Game Tester', 'Game Producer', 'Game Director', '3D Artist', '2D Artist', 'Animator', 'Concept Artist', 'Technical Artist', 'Art director', 'Game Programmer', 'Tools Programmer', 'Engine Programmer', 'Graphics Programmer', 'Computer Graphics and Sound Artist', 'Graphics Creator', 'Group Lead Artist Graphic', 'Video Game Artist', 'Computer Graphics Artist', 'Visual Effects Artist', 'Animation Supervisor', 'Creative Artist', 'Digital Game Artist'],
        
        'Creative Content Designers Professionals':['Web Designer', 'Graphic Designer', 'Typographical Designer', 'Designer', 'Multimedia Designer', 'Publication Designer', 'Virtual Environment Designer', 'Creative Designer', 'Character Designer', 'Flash Designer', 'Interface Designer', 'Systems/Computer Designer', 'UI Designer', 'UX Designer', 'Design Architect', 'Digital Designer', 'Creative Team Leader', 'Character Rigger', 'System Technical Writer', 'Content Editor', 'Business Intelligence Analyst', 'Business Process Specialist', 'Content Reviewer', 'Content Coordinator'],
        
        'Computer Network and Systems Technicians':['Computer Network Technician', 'Network Support Technician', 'Network Security Technician', 'System Security  & Application ICT Technician', 'Assistant Network Engineer', 'Assistant Security Officer'],
        
        'Applications Programmers':['Computer Programmer', 'Software Programmer', 'Technical Programmer', 'Information Technology Programmer', 'Communication Programmer', 'Database Programmer', 'Systems Programmer', 'Analyst Programmer', 'Applications Programmer', '.NetAnalyst Programmer', 'Lotus Notes Programmer', 'Video Game Programmer', 'Network Programmer', 'Sound Programmer', 'Artificial Intelligence Programmer', 'Analog Integrated Circuit Design Verification Engineer', '.Net Programmer', 'Software Programme', 'C/C++ Programmer', 'C++ Graphics Programmer', 'Cobol Programmer', 'JavaScript Programmer', 'J2EE Programmer', 'J2ME Programmer', 'Java EE Programmer', 'Hypertext Preprocessor Programmer', 'Animation Programmer', 'Computer Games Programmer', 'Multimedia Programmer', 'Navision Analyst Programmer', 'Java Analyst Programmer', 'Database Application Specialist', 'Computer Infrastructure Specialist', 'UI/ Gameplay Coders', 'Game Engine Programmers', 'E-Commerce Web Programmer', 'Tools Programmer', 'C++ Software Analyst', '.Net Programmer Analyst', 'Enterprise Resource Planning Programmer Analyst', 'Java Programmer Analyst', 'Oracle Application Analyst'],    
    }        
            
    object_list=[]
    for job_key in jobs:
        if keywords == job_key:
            for word in jobs[job_key]:
                jobs_list = job.objects.filter(title__icontains=word).order_by('-creation_date')
                for i in jobs_list:
                    if i not in object_list:
                       object_list.append(i)
        
    if request.method == "POST":
        request.session['name'] = request.POST['name']
        request.session['location'] = request.POST['location']
        name=request.session['name']
        location=request.session['location']
        
        for hist in history:
            if (name==hist.name and location==hist.location):
                count=count+1
                break
            else:
                count=0
        if(count!=1):
            searchitem=searchTerm.objects.create(user=student.objects.get(name=request.user),name=name,location=location)
            searchitem.save()  
                  
        return redirect("user_search_result")
    return render(request,'user_homepage.html',{'jobs':object_list})

def company_detail(request,id):
    if request.method=="POST":
        if 'login' in request.POST:
            request.session['email'] = request.POST['email']
            request.session['password'] = request.POST['password']
            return redirect('home')
    
    companys=company.objects.get(id=id)
    reviews=review.objects.filter(company=companys)
    avg_rating=review.objects.filter(company=companys).aggregate(avg=Avg('score'))
    avg_rating_avg=avg_rating.get('avg',0.0)
    if avg_rating_avg != None:
        avg_rating_avg=avg_rating.get('avg',0.0).__round__(1)
    else:
        avg_rating_avg= 0.0
    companys.avg_rating=avg_rating_avg
    companys.save()
    
    return render(request,'company_detail.html',{'reviews':reviews,'company':companys,'avg_rating':avg_rating})

def user_companies(request):
    if not request.user.is_authenticated:
        return redirect('home')
    companys=list(company.objects.all())
    reviews=list(review.objects.all().order_by('-company__avg_rating'))
    empty_list=[]
    non_empty_list=[]
    if reviews==[]:
        for i in companys:
            empty_list.append(i)
    else:
        for rev in reviews:
            for i in companys:
                if rev.company != i:
                    if i not in empty_list:
                        empty_list.append(i)
                else:
                    if i not in non_empty_list:
                        non_empty_list.append(i)
    empty_list=[i for i in empty_list if i not in non_empty_list]
    return render(request,"user_companies.html",{'company_reviews1':empty_list,'company_reviews2':non_empty_list})

def user_review(request,id):
    if not request.user.is_authenticated:
        return redirect('home')

    reviews=company.objects.get(id=id)
    students=student.objects.get(name=request.user)
    
    if review.objects.filter(student=students,company=reviews):
        messages.error(request,"One user only can comment one time!")
        return redirect('user_company_detail',id)
    else:
        if request.method == "POST":
            head= request.POST['title']
            good=request.POST['good']
            bad=request.POST['bad']
            additional=request.POST['additional']
            score=request.POST['rate']
            review.objects.create(company=reviews,student=students,creation_date=date.today(),score=score,head=head,good=good,bad=bad,additional=additional)
            return redirect('user_company_detail',id)
    return render(request,'user_review.html',{'company':reviews})

def user_company_detail(request,id):
    if not request.user.is_authenticated:
        return redirect('home')
    
    companys=company.objects.get(id=id)
    reviews=review.objects.filter(company=companys).order_by('-creation_date')
    avg_rating=review.objects.filter(company=companys).aggregate(avg=Avg('score'))
    avg_rating_avg=avg_rating.get('avg',0.0)
    if avg_rating_avg != None:
        avg_rating_avg=avg_rating.get('avg',0.0).__round__(1)
    else:
        avg_rating_avg= 0.0
    companys.avg_rating=avg_rating_avg
    companys.save()

    return render(request,'user_company_detail.html',{'reviews':reviews,'company':companys,'avg_rating':avg_rating})

def user_review_list(request):
    if not request.user.is_authenticated:
        return redirect('home')

    students=student.objects.get(name=request.user)
    reviews=review.objects.filter(student=students)
    return render(request,"user_review_list.html",{'reviews':reviews})

def about_us(request):
    if request.method=="POST":
        if 'login' in request.POST:
            request.session['email'] = request.POST['email']
            request.session['password'] = request.POST['password']
            return redirect('home')
    return render(request,"about_us.html")

def user_about_us(request):
    if not request.user.is_authenticated:
        return redirect('home')

    return render(request,"user_about_us.html")

def company_own_review(request,id):
    if not request.user.is_authenticated:
        return redirect('home')

    companys=company.objects.get(id=id)
    reviews=review.objects.filter(company=companys)
    return render(request,'company_own_review.html',{'company':companys,'reviews':reviews})

def feedbacks(request):
    popup=False
    if request.method =="POST":
        email=request.POST['email']
        title=request.POST['title']
        description=request.POST['description']
        popup=True
        feedbacks=feedback.objects.create(email=email,title=title,content=description,created_date=date.today())
        feedbacks.save()
    return render(request,"feedback.html",{'popup':popup})

def user_feedbacks(request):
    if not request.user.is_authenticated:
        return redirect('home')

    students=student.objects.get(user=request.user)
    popup=False
    if request.method =="POST":
        title=request.POST['title']
        description=request.POST['description']
        popup=True
        feedbacks=feedback.objects.create(email=students.email,title=title,content=description,created_date=date.today())
        feedbacks.save()
    return render(request,"user_feedback.html",{'user':students,'popup':popup})

def company_feedbacks(request):
    if not request.user.is_authenticated:
        return redirect('home')

    companys=company.objects.get(user=request.user)
    popup=False
    if request.method =="POST":
        title=request.POST['title']
        description=request.POST['description']
        popup=True
        feedbacks=feedback.objects.create(email=companys.email,title=title,content=description,created_date=date.today())
        feedbacks.save()
    return render(request,"company_feedback.html",{'company':companys,'popup':popup})

def user_test(request):
    if request.method =="POST": 
        array=[] 
        for i in range(20):
            ans = request.POST.get('q'+str(i+1))
            array.extend(ans.split())
             
        if CareerTest.objects.filter(user=student.objects.get(name=request.user)).exists(): 
            up_Test=CareerTest.objects.get(user=student.objects.get(name=request.user))
            up_Test.q1=array[0]
            up_Test.q2=array[1]
            up_Test.q3=array[2]
            up_Test.q4=array[3]
            up_Test.q5=array[4]
            up_Test.q6=array[5]
            up_Test.q7=array[6]
            up_Test.q8=array[7]
            up_Test.q9=array[8]
            up_Test.q10=array[9]
            up_Test.q11=array[10]
            up_Test.q12=array[11]
            up_Test.q13=array[12]
            up_Test.q14=array[13]
            up_Test.q15=array[14]
            up_Test.q16=array[15]
            up_Test.q17=array[16]
            up_Test.q18=array[17]
            up_Test.q19=array[18]
            up_Test.q20=array[19]
            up_Test.save()
        else:                            
            test = CareerTest.objects.create(user=student.objects.get(name=request.user),q1=array[0],q2=array[1],q3=array[2],q4=array[3],q5=array[4],q6=array[5],q7=array[6],q8=array[7],q9=array[8],q10=array[9],q11=array[10],q12=array[11],q13=array[12],q14=array[13],q15=array[14],q16=array[15],q17=array[16],q18=array[17],q19=array[18],q20=array[19])
            test.save()
            
        return redirect("user_homepage")            
    return render(request,"user_test.html")