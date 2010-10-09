#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from django.db import IntegrityError


class RegisterHandler(KeywordHandler):
    """
    Allow remote users to register themselves, by creating a Contact
    object and associating it with their Connection. For example:

        >>> RegisterHandler.test('join Adam Mckaig amckaig')
        ['Thank you for registering, Adam Mckaig! Your username is amckaig']

        >>> Contact.objects.filter(name="Adam Mckaig")
        [<Contact: Adam Mckaig>]
    """

    keyword = "register|reg|r|join"

    def help(self):
        self.respond("To register, send reg <NAME>")

    def handle(self, text):
        info = text.rpartition(' ')

        #check that the alias is not in use already
        try:
            new_contact = Contact.objects.create(name=info[0], alias = info[1].lower())
        except IntegrityError:
            self.respond("Alias %s is already in use, please try again." % new_alias)
        else:
            self.msg.connection.contact = new_contact
            self.msg.connection.save()
            self.respond(
            "Thank you for registering, %(name)s! Your username is %(alias)s.",
            name=new_contact.name, alias=new_contact.alias)
