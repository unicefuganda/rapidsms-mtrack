from django.db.models.signals import pre_save, post_save
from rapidsms_xforms.models import xform_received
from healthmodels.models import HealthFacility, HealthFacilityType
from healthmodels.models.HealthFacility import HealthFacilityBase
from logistics.models import SupplyPoint, SupplyPointType
from mtrack.loader import create_supply_point_from_facility, get_location_from_facility

def xform_received_handler(sender, **kwargs):
    from logistics.models import ProductReportsHelper
    from logistics.util import config
    from logistics import const
    xform = kwargs['xform']
    submission = kwargs['submission']
    message = None
    if 'message' in kwargs:
        message = kwargs['message']
    try:
        message = message.db_message
        health_provider = submission.connection.contact.healthproviderbase.healthprovider
    except:
        return

    if not message or health_provider.facility is None:
        return

    if xform.keyword == 'act':
        stock_report = ProductReportsHelper(health_provider.facility.supply_point,
                                            const.Reports.SOH,
                                            message)

        stock_report.add_product_receipt(config.Products.SIX_PACK, submission.eav.act_spd)
        stock_report.add_product_stock(config.Products.SIX_PACK, submission.eav.act_sps)
        stock_report.add_product_receipt(config.Products.TWELVE_PACK, submission.eav.act_tpd)
        stock_report.add_product_stock(config.Products.TWELVE_PACK, submission.eav.act_tps)
        stock_report.add_product_receipt(config.Products.EIGHTEEN_PACK, submission.eav.act_epd)
        stock_report.add_product_stock(config.Products.EIGHTEEN_PACK, submission.eav.act_eps)
        stock_report.add_product_receipt(config.Products.TWENTY_FOUR_PACK, submission.eav.act_fpd)
        stock_report.add_product_stock(config.Products.TWENTY_FOUR_PACK, submission.eav.act_fps)
        stock_report.save()
    elif xform.keyword == 'qun':
        stock_report = ProductReportsHelper(health_provider.facility.supply_point,
                                            const.Reports.SOH,
                                            message)

        stock_report.add_product_receipt(config.Products.OTHER_ACT_STOCK, submission.eav.qun_oad)
        stock_report.add_product_stock(config.Products.OTHER_ACT_STOCK, submission.eav.qun_oas)
        stock_report.add_product_receipt(config.Products.QUININE, submission.eav.qun_qud)
        stock_report.add_product_stock(config.Products.QUININE, submission.eav.qun_qus)
        stock_report.save()

    elif xform.keyword == 'rdt':
        stock_report = ProductReportsHelper(health_provider.facility.supply_point,
                                            const.Reports.SOH,
                                            message)

        stock_report.add_product_receipt(config.Products.RAPID_DIAGNOSTIC_TEST, submission.eav.rdt_rdd)
        stock_report.add_product_stock(config.Products.RAPID_DIAGNOSTIC_TEST, submission.eav.rdt_rds)
        stock_report.save()

    return

xform_received.connect(xform_received_handler, weak=True)

def update_supply_point_from_facility(sender, instance, **kwargs):
    """ 
    whenever a facility is updated, automatically update the supply point
    """
    try:
        supply_point = instance.supply_point
    except SupplyPoint.DoesNotExist:
        # TODO: LOG AN ERROR?
        supply_point = None
    try:
        base = HealthFacilityBase.objects.get(pk=instance.pk)
    except HealthFacilityBase.DoesNotExist:
        base = instance
    if supply_point is None:
        # create
        instance.supply_point = create_supply_point_from_facility(base)
        return

    # else update
    try:
        type_, created = SupplyPointType.objects.get_or_create(code=base.type.slug)
    except HealthFacilityType.DoesNotExist:
        # TODO: LOG AN ERROR?
        type_, created = SupplyPointType.objects.get_or_create(code='UNKNOWN')
    supply_point.type = type_
    try:
        supply_point.location = get_location_from_facility(base)
    except ValueError:
        pass
    supply_point.save()
    return

post_save.connect(update_supply_point_from_facility, HealthFacility)
