#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from pikwa.retail.models import Organization 
from django.db import IntegrityError


class RegisterHandler(KeywordHandler):
    """
    Allow remote users to register themselves, by creating a Contact
    object and associating it with their Connection and an existing organization. For example:

        >>> RegisterHandler.test('join Adam Mckaig amckaig unicef')
        ['Thank you for registering, Adam Mckaig! Your username is amckaig']

        >>> Contact.objects.filter(name="Adam Mckaig")
        [<Contact: Adam Mckaig>]
    """

    keyword = "register|reg|r|join"

    def help(self):
        self.respond("To register, send reg <NAME> <ALIAS> <ORGANIZATION>")

    def handle(self, text):
        info = text.split(' ')
        org_code = info.pop().upper()
        alias = info.pop().lower()
        name = ' '.join(i.capitalize() for i in info)

        #check that the requested organization exists
        existing = Organization.objects.filter(code=org_code)
        if not existing:
            self.respond("Organization %s not found, please try again." % org_code)
            return True
        else:
            org = Organization.objects.get(code=org_code)

        #check that the alias is not in use already
        existing = Contact.objects.filter(alias=alias)
        if not existing:
            new_contact = Contact.objects.create(name = name, alias = alias, organization = org)
            self.msg.connection.contact = new_contact
            self.msg.connection.save()
            self.respond(
            "Thank you for registering, %(name)s! Your username is %(alias)s and your organization is %(org)s.",
            name=new_contact.name, alias=new_contact.alias, org=new_contact.organization)
        else:
            self.respond("Alias %s is already in use, please try again." % alias)

