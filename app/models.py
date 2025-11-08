from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    # User information
    USER = (
        ('1', 'hoo'),
        ('2', 'sysadmin'),
        ('3',  'municipaladmin'),
        ('4', 'admincenter'),
        ('5', 'centerstaff'),
    )
    user_type = models.CharField(choices=USER, max_length=25)
    profile_pic = models.ImageField(upload_to='profile_pic/')
    email = models.EmailField(max_length=150, unique=True)
    
 
class RfidAuth(models.Model):
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
        return self.province_name
    

class Municipality(models.Model):
    municipality_name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.municipality_name
    
    
class Barangay(models.Model):
    barangay_name = models.CharField(max_length=100)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.barangay_name
    
 
class Registration(models.Model):
    rfid = models.CharField(max_length=50, unique=True)

    last_name = models.CharField(max_length=100)         
    first_name = models.CharField(max_length=100)         
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    name_extension = models.CharField(max_length=10, blank=True, null=True)  # Jr, Sr...

    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=255)

    province = models.ForeignKey(Province, on_delete=models.CASCADE) 
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE)

    mobile_no = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, blank=True, null=True)
    civil_status = models.CharField(max_length=20, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True, unique=True)

    date_added = models.DateTimeField(auto_now_add=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name} {self.middle_name or ''}".strip()
    

class Medicines(models.Model):
    medicine_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    date_expiry = models.DateField()
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.medicine_name

class Bsrcenter(models.Model):
    tracking_number = models.CharField(max_length=100, unique=True , blank=True, null=True)
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    age = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_claimed = models.DateField(auto_now_add=True)
    date_claim_expiry = models.DateField()
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    barangay_indigency = models.BooleanField(default=False)
    barangay_recidency = models.BooleanField(default=False)
    diagnosis = models.TextField (blank=True, null=True)
    
    def __str__(self):
        # Bsrcenter no longer stores a direct medicines FK on the model;
        # show registration and tracking number (or id) for readability.
        return f"{self.registration} - {self.tracking_number or self.id}"

class Bsrcenter_meds(models.Model):
    bsrcenter = models.ForeignKey(Bsrcenter, on_delete=models.CASCADE)
    medicines = models.ForeignKey(Medicines, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.bsrcenter.registration} - {self.medicines.medicine_name}"


class Bsrcenter_Burial(models.Model):
    tracking_number = models.CharField(max_length=100, unique=True , blank=True, null=True)
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    deceased_name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100)
    date_claimed = models.DateField(auto_now_add=True)
    date_claim_expiry = models.DateField()
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    death_certificate = models.BooleanField(default=False)
    cause_of_death = models.TextField (blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.registration} - {self.tracking_number or self.id}"
    

