from django.db import models
from django.db.models.signals import post_save
from django.contrib.admin.models import User
from datetime import datetime

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
    seller       = models.ForeignKey('rapidsms.Contact')
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

    REGION_CHOICES = (
        (101,  'Kalangala'),
        (102,  'Kampala'),
        (103,  'Kiboga'),
        (104,  'Luwero'),
        (105,  'Masaka'),
        (106,  'Mpigi'),
        (107,  'Mubende'),
        (108,  'Mukono'),
        (109,  'Nakasongola'),
        (110,  'Rakai'),
        (111,  'Sembabule'),
        (112,  'Kayunga'),
        (113,  'Wakiso'),
        (114,  'Mityana'),
        (115,  'Nakaseke'),
        (116,  'Lyantonde'),
        (201,  'Bugiri'),
        (202,  'Busia'),
        (203,  'Iganga'),
        (204,  'Jinja'),
        (205,  'Kamuli'),
        (206,  'Kapchorwa'),
        (207,  'Katakwi'),
        (208,  'Kumi'),
        (209,  'Mbale'),
        (210,  'Pallisa'),
        (211,  'Soroti'),
        (212,  'Tororo'),
        (213,  'Kaberamaido'),
        (214,  'Mayuge'),
        (215,  'Sironko'),
        (216,  'Amuria'),
        (217,  'Budaka'),
        (218,  'Bukwa'),
        (219,  'Butaleja'),
        (220,  'Kaliro'),
        (221,  'Manafwa'),
        (222,  'Namutumba'),
        (223,  'Bududa'),
        (224,  'Bukedea'),
        (301,  'Adjumani'),
        (302,  'Apac'),
        (303,  'Arua'),
        (304,  'Gulu'),
        (305,  'Kitgum'),
        (306,  'Kotido'),
        (307,  'Lira'),
        (308,  'Moroto'),
        (309,  'Moyo'),
        (310,  'Nebbi'),
        (311,  'Nakapiripirit'),
        (312,  'Pader'),
        (313,  'Yumbe'),
        (314,  'Amolatar'),
        (315,  'Kaabong'),
        (316,  'Koboko'),
        (317,  'Abim'),
        (318,  'Dokolo'),
        (319,  'Amuru'),
        (320,  'Maracha'),
        (321,  'Oyam'),
        (401,  'Bundibugyo'),
        (402,  'Bushenyi'),
        (403,  'Hoima'),
        (404,  'Kabale'),
        (405,  'Kabarole'),
        (406,  'Kasese'),
        (407,  'Kibaale'),
        (408,  'Kisoro'),
        (409,  'Masindi'),
        ('410',  'Mbarara'),
        (411,  'Ntungamo'),
        (412,  'Rukungiri'),
        (413,  'Kamwenge'),
        (414,  'Kanungu'),
        (415,  'Kyenjojo'),
        (416,  'Ibanda'),
        (417,  'Isingiro'),
        (418,  'Kiruhura'),
        (419,  'Buliisa'),
    )    
    
    serial = models.CharField(max_length=14, help_text="Product serial number", primary_key=True)
    product      = models.ForeignKey(Product)
    purchase_date     = models.DateTimeField()
    fname             = models.CharField(max_length=20, help_text="Owner first name", verbose_name="First Name")
    lname             = models.CharField(max_length=20, help_text="Owner last name", verbose_name="Last Name")
    pri_phone         = models.CharField(max_length=16, help_text ="Owner primary phone number", verbose_name="Primary Phone")
    sec_phone         = models.CharField(max_length=16, null = True, blank = True, help_text ="Owner secondary phone number (optional)", verbose_name="Secondary Phone")
    purchase_price    = models.DecimalField(max_digits=5, decimal_places=2, help_text="Purchase price of stove")
    region            = models.CharField(choices = REGION_CHOICES, max_length=3)
    description       = models.CharField(max_length=50, help_text="Village name or other description of user's location")    
    seller            = models.ForeignKey('rapidsms.Contact')
    
    def __unicode__(self):
        return self.serial

    def save(self):
        #update the seller's revenue total
        self.seller.cached_revenue += (self.purchase_price * 1000)
        self.seller.save()
        #update the seller's stock
        current_stock = Stock.get_existing(self.seller.alias, self.product.code)
        current_stock.stock_amount -= 1
        current_stock.save()
        #now save the sale itself        
        super(Sale, self).save()
    
    @classmethod
    def by_serial (cls, serial):
        try:
            return cls.objects.get(serial=serial.lower())
        except models.ObjectDoesNotExist:
            return None

class StockTransaction(models.Model):

    CANCELLED = 3
    PENDING = 2
    ACCEPTED = 1
    REJECTED = 0
    
    STATUS_CHOICES = (
        (CANCELLED, 'Canceled'),
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
    )
    
    to_transfer = models.ManyToManyField(Stock)
    initiator = models.ForeignKey('rapidsms.Contact', related_name='stocktransaction_initiators')
    recipient = models.ForeignKey('rapidsms.Contact', related_name='stocktransaction_recipients')
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
