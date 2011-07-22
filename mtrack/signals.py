from django.db.models.signals import pre_save
from rapidsms_xforms.models import xform_received
from healthmodels.models import HealthFacility
from logistics.models import SupplyPoint, SupplyPointType
from mtrack.loader import create_supply_point_from_facility, get_location_from_facility

def xform_received_handler(sender, **kwargs):
    from logistics.models import ProductReportsHelper
    from logistics.util import config
    from logistics import const
    xform = kwargs['xform']
    submission = kwargs['submission']
    #why am i getting errors?
    #if submission.has_errors:
    #    return
    
    message = None
    if 'message' in kwargs:
        message = kwargs['message']
    try:
        message = message.db_message
    except AttributeError:
        return
    if not message:
        return
    
    try:
        health_provider = submission.connection.contact.healthproviderbase.healthprovider
    except:
        submission.response = "Must be a reporter. Please register first with your name."
        submission.has_errors = True
        submission.save()
        return
    
    if xform.keyword == 'act':
        if health_provider.facility is None:
            submission.response = "You are not associated with a facility. Please contact an administrator."
            submission.has_errors = True
            submission.save()
            return
        stock_report = ProductReportsHelper(health_provider.facility.supply_point, 
                                            const.Reports.SOH,  
                                            message)
        stock_report.add_product_receipt(config.Products.YELLOW_ACT, submission.eav.act_yellow_disp)
        stock_report.add_product_stock(config.Products.YELLOW_ACT, submission.eav.act_yellow_balance)
        stock_report.add_product_receipt(config.Products.BLUE_ACT, submission.eav.act_blue_disp)
        stock_report.add_product_stock(config.Products.BLUE_ACT, submission.eav.act_blue_balance)
        stock_report.add_product_receipt(config.Products.BROWN_ACT, submission.eav.act_brown_disp)
        stock_report.add_product_stock(config.Products.BROWN_ACT, submission.eav.act_brown_balance)
        stock_report.add_product_receipt(config.Products.GREEN_ACT, submission.eav.act_green_disp)
        stock_report.add_product_stock(config.Products.GREEN_ACT, submission.eav.act_green_balance)
        stock_report.add_product_receipt(config.Products.OTHER_ACT, submission.eav.act_other_disp)
        stock_report.add_product_stock(config.Products.OTHER_ACT, submission.eav.act_other_balance)
        stock_report.save()
        submission.response = "Thank you for reporting your stock on hand"
        submission.save()
        return

xform_received.connect(xform_received_handler, weak=True)

def update_supply_point_from_facility(sender, instance, **kwargs): 
    """ 
    whenever a facility is updated, automatically update the supply point
    """
    supply_point = instance.supply_point
    if supply_point is None:
        # create
        instance.supply_point = create_supply_point_from_facility(instance)
        return
    # else update
    type_, created = SupplyPointType.objects.get_or_create(code=instance.type.slug)
    supply_point.type = type_
    try:
        supply_point.location = get_location_from_facility(instance)
    except ValueError:
        pass
    supply_point.save()
    return
    
pre_save.connect(update_supply_point_from_facility, HealthFacility)
