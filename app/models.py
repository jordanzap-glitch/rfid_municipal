from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    # User information
    USER = (
        (1, 'hoo'),
        (2, 'sysadmin'),
        (3, 'subadmin'),
    )
    user_type = models.CharField(choices=USER, max_length=25)
    profile_pic = models.ImageField(upload_to='profile_pic/')
    email = models.EmailField(max_length=150, unique=True)
    
 
class RifdAuth(models.Model):
    STATUS_CHOICES = (
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
    )
    rfid = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='valid')
    in_use = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.rfid} - {self.status} - {'In Use' if self.in_use else 'Not In Use'}"
    
    
class Province(models.Model):
    province_name = models.CharField(max_length=100)

    def __str__(self):
        return self.province_namename
    

class Municipality(models.Model):
    municipality_name = models.CharField(max_length=100)
    province_id = models.ForeignKey(Province, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.municipality_name
    
    
class Barangay(models.Model):
    barangay_name = models.CharField(max_length=100)
    municipality_id = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.barangay_name
    
 
class Registration(models.Model):
    rfid = models.CharField(max_length=50, unique=True, blank=True, null=True)

    l_name = models.CharField(max_length=100)         
    f_name = models.CharField(max_length=100)         
    m_name = models.CharField(max_length=100, blank=True, null=True)
    name_extension = models.CharField(max_length=10, blank=True, null=True)  # Jr, Sr...

    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=255)

    province_id = models.ForeignKey(Province, on_delete=models.CASCADE) 
    municipality_id = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    barangay_id = models.ForeignKey(Barangay, on_delete=models.CASCADE)

    mobile_no = models.CharField(max_length=20)

    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.l_name}, {self.f_name} {self.m_name or ''}".strip()   

