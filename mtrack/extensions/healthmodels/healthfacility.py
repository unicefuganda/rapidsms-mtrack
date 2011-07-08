#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from logistics.models import SupplyPoint

class FacilityWithDrugs(SupplyPoint):
    class Meta:
        abstract = True