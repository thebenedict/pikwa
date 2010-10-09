#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact

class GrantManagerHandler(KeywordHandler):
    """
    Used by administrators to give manager permissions to another user (the target).

    """

    keyword = "admin|manager|m"

    def help(self):
        user = self.msg.connection.contact
        if not user.role:
            self.respond("You do not have permission to use this command.")
        else:
            self.respond("Usage: m (username). Example: m dnombo")

    def handle(self, target_alias):
        user = self.msg.connection.contact
        if not user.role:
            self.respond("You do not have permission to use this command.")
            return True

        # confirm that alias exists
        try:
            target = Contact.objects.get(alias=target_alias)
        except:
            self.respond("Sorry, user %s was not found. Please check your spelling and try again." % target_alias)
            return True

        target.role = 1
        target.save()

        #notify target of their new role
        target.message("You have been made a manager by %s." % user.alias)

        self.respond("%s has been made a manager." % target.alias)
