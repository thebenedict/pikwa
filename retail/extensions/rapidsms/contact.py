from django.db import models

class MobileUser(models.Model):
    
    ADMIN = 2
    MANAGER = 1
    SELLER = 0    

    ROLE_CHOICES = (
        (SELLER, 'Seller'),
        (MANAGER, 'Manager'),
        #(ADMIN, 'Administrator'),
    )

    role = models.IntegerField(choices = ROLE_CHOICES, default = SELLER)
    alias = models.CharField(max_length = 12, unique = True, \
                             help_text = "Unique username, 12 characters, no spaces")
    organization = models.ForeignKey('retail.Organization')

    @classmethod
    def by_alias (cls, alias):
        try:
            return cls.objects.get(alias=alias)
        except models.ObjectDoesNotExist:
            return None

class Meta:
    abstract = True


