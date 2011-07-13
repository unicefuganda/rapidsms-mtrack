#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from logistics.models import SupplyPoint

class FacilityWithDrugs(models.Model):
    supply_point = models.ForeignKey("logistics.SupplyPoint", null=True, blank=True)
    
    class Meta:
        abstract = True
