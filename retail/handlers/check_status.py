#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import locale
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from retail.models import Sale

class StatusHandler(KeywordHandler):
    """
    Allow remote users to request information about a sale by SN.
    """

    keyword = "check|chk|ck|c"

    def help(self):
        self.respond("Usage: c (serial number)\nExample: c EC12345")
    

    def handle(self, serial):
        s = Sale.by_serial(serial)
        if s:
            locale.setlocale( locale.LC_ALL, '')
            self.respond("%s: %s Tsh paid on %s. Owner: %s %s (%s) %s, %s" % (s.serial, locale.format('%d', s.purchase_price*1000, True), s.purchase_date.strftime("%d-%m-%y"), s.fname, s.lname, s.pri_phone, s.get_region_display(), s.description))
        else:
            self.respond("Serial number %s not recognized" % serial)
