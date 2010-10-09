from django.db import models
from django.db.models.signals import post_save
from django.contrib.admin.models import User
from datetime import datetime
from rapidsms.models import Contact

class Product(models.Model):
    code = models.CharField(max_length=4, \
                            help_text="Product abbreviation, max 4 characters")
    display_name = models.CharField(max_length=15, \
                            help_text=("Short name for use in SMS"));
    full_name = models.CharField(max_length=100,blank=True, null=True)

    def __unicode__(self):
        return self.display_name

    @classmethod
    def by_code (cls, code):
        try:
            return cls.objects.get(code=code)
        except models.ObjectDoesNotExist:
            return None

class Stock(models.Model): 
    seller       = models.ForeignKey(Contact)
    product      = models.ForeignKey(Product)
    stock_amount = models.IntegerField(default=0)
    
    def __unicode__(self):
        return "%s: %s %ss" % (
            self.seller.alias,
            self.stock_amount,
            self.product.display_name)

    @classmethod
    def get_existing (cls, alias, code):
        try:
            return cls.objects.get(seller__alias=alias,product__code=code)
        except models.ObjectDoesNotExist:
            return None

class Sale(models.Model):
    
    ARUSHA = 'A'
    DAR_ES_SALAAM = 'B'
    DODOMA = 'C'
    IRINGA = 'D'
    KAGERA = 'E'
    KIGOMA = 'F'
    KILIMANJARO = 'G'
    LINDI = 'H'
    MANYARA = 'I'
    MARA = 'J'
    MBEYA = 'K'
    MOROGORO = 'L'
    MTWARA = 'M'
    MWANZA = 'N'
    PEMBA_NORTH = 'O'
    PEMBA_SOUTH = 'P'
    PWANI = 'Q'
    RUKWA = 'R'
    RUVUMA = 'S'
    SHINYANGA = 'T'
    SINGIDA = 'U'
    TABORA = 'V'
    TANGA = 'W'
    ZANZIBAR_CENTRAL_SOUTH = 'X'
    ZANZIBAR_NORTH = 'Y'
    ZANZIBAR_URBAN_WEST = 'Z'

    REGION_CHOICES = (
        (ARUSHA,  'Arusha'),
        (DAR_ES_SALAAM,  'Dar Es Salaam'),
        (DODOMA,  'Dodoma'),
        (IRINGA,  'Iringa'),
        (KAGERA,  'Kagera'),
        (KIGOMA,  'Kigoma'),
        (KILIMANJARO,  'Kilimanjaro'),
        (LINDI,  'Lindi'),
        (MANYARA,  'Manyara'),
        (MARA,  'Mara'),
        (MBEYA,  'Mbeya'),
        (MOROGORO,  'Morogoro'),
        (MTWARA,  'Mtwara'),
        (MWANZA,  'Mwanza'),
        (PEMBA_NORTH,  'Pemba North'),
        (PEMBA_SOUTH,  'Pemba South'),
        (PWANI,  'Pwani'),
        (RUKWA,  'Rukwa'),
        (RUVUMA,  'Ruvuma'),
        (SHINYANGA,  'Shinyanga'),
        (SINGIDA,  'Singida'),
        (TABORA,  'Tabora'),
        (TANGA,  'Tanga'),
        (ZANZIBAR_CENTRAL_SOUTH,  'Zanzibar Central/South'),
        (ZANZIBAR_NORTH,  'Zanzibar North'),
        (ZANZIBAR_URBAN_WEST,  'Zanzibar Urban/West'),
    )    
    
    serial = models.CharField(max_length=14, help_text="Product serial number", primary_key=True)
    product      = models.ForeignKey(Product)
    purchase_date     = models.DateTimeField()
    fname             = models.CharField(max_length=20, help_text="Owner first name", verbose_name="First Name")
    lname             = models.CharField(max_length=20, help_text="Owner last name", verbose_name="Last Name")
    pri_phone         = models.CharField(max_length=16, help_text ="Owner primary phone number", verbose_name="Primary Phone")
    sec_phone         = models.CharField(max_length=16, null = True, blank = True, help_text ="Owner secondary phone number (optional)", verbose_name="Secondary Phone")
    purchase_price    = models.DecimalField(max_digits=5, decimal_places=2, help_text="Purchase price of stove")
    region            = models.CharField(choices = REGION_CHOICES, max_length=1)
    description       = models.CharField(max_length=50, help_text="Village name or other description of user's location")    
    seller            = models.ForeignKey(Contact)
    
    def __unicode__(self):
        return self.serial
    
    @classmethod
    def by_serial (cls, serial):
        try:
            return cls.objects.get(serial=serial.upper())
        except models.ObjectDoesNotExist:
            return None

class StockTransaction(models.Model):

    PENDING = 2
    ACCEPTED = 1
    REJECTED = 0
    
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
    )
    
    to_transfer = models.ManyToManyField(Stock)
    initiator = models.ForeignKey(Contact, related_name='stocktransaction_initiators')
    recipient = models.ForeignKey(Contact, related_name='stocktransaction_recipients')
    status = models.IntegerField(choices = STATUS_CHOICES, max_length=1)
    date_initiated = models.DateTimeField()
    date_resolved = models.DateTimeField(null=True, blank=True)
    
    def __unicode__(self):
        return "%s -> %s: %s" % (
            self.initiator.alias,
            self.recipient.alias,
            self.status)
            
    @classmethod
    def by_recipient (cls, recip):
        try:
            return cls.objects.get(recipient = recip, status = PENDING)
        except models.ObjectDoesNotExist:
            return None

class Organization(models.Model):
    code = models.CharField(max_length=4, \
                            help_text="Organization abbreviation, max 4 characters")
    display_name = models.CharField(max_length=15, \
                            help_text=("Short name for use in SMS"));
    full_name = models.CharField(max_length=100,blank=True, null=True)

    def __unicode__(self):
        return self.full_name

    @classmethod
    def by_code (cls, code):
        try:
            return cls.objects.get(code=code)
        except models.ObjectDoesNotExist:
            return None

class UserProfile(models.Model):
    user = models.ForeignKey(User)
    organization = models.ForeignKey(Organization, blank=True, null=True)

    def __str__(self):
        return "Profile for %s" % self.user

def create_user_profile(sender, instance, created, **kwargs):  
    if created:  
       profile, created = UserProfile.objects.get_or_create(user=instance) 

post_save.connect(create_user_profile, sender=User)
