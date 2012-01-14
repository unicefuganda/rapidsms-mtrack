import logging
from django.db.models.signals import pre_save, post_save
from rapidsms_xforms.models import xform_received
from healthmodels.models import HealthFacility, HealthFacilityType
from healthmodels.models.HealthFacility import HealthFacilityBase
from logistics.models import SupplyPoint, SupplyPointType
from mtrack.loader import create_supply_point_from_facility, get_location_from_facility

stock_reports = ['act', 'qun', 'rdt']

def xform_received_handler(sender, **kwargs):
    xform = kwargs['xform']
    if xform.keyword not in stock_reports:
        return
    submission = kwargs['submission']
    process_xform(submission)
    
def process_xform(submission):
    from logistics.models import ProductReportsHelper
    from logistics.util import config
    from logistics import const
    try:
        health_provider = submission.connection.contact.healthproviderbase.healthprovider
    except:
        logging.error('%s contact is not a health provider' % submission.connection.identity)
        return
    if not submission.message:
        logging.error('%s sent an empty message' % submission.connection.identity)
        return
    if health_provider.facility is None:
        logging.error('%s has no associated facility' % submission.connection.identity)
        return

    values_count = len(submission.submission_values())
    try:
        if submission.xform.keyword == stock_reports[0]:
            required_length = len(config.Products.ACT_REPORT) * 2
            if values_count != required_length:
                if values_count < required_length:
                    submission.response = "This is an incomplete report. Please submit ALL of your ACT stock data in the form 'act 1 2 3 4 5 6 7 8'"
                submission.has_errors = True
                submission.save()
                return
            stock_report = ProductReportsHelper(health_provider.facility.supply_point,
                                                const.Reports.SOH,
                                                submission.message)
            stock_report.add_product_receipt(config.Products.SIX_PACK, submission.eav.act_spd)
            stock_report.add_product_stock(config.Products.SIX_PACK, submission.eav.act_sps)
            stock_report.add_product_receipt(config.Products.TWELVE_PACK, submission.eav.act_tpd)
            stock_report.add_product_stock(config.Products.TWELVE_PACK, submission.eav.act_tps)
            stock_report.add_product_receipt(config.Products.EIGHTEEN_PACK, submission.eav.act_epd)
            stock_report.add_product_stock(config.Products.EIGHTEEN_PACK, submission.eav.act_eps)
            stock_report.add_product_receipt(config.Products.TWENTY_FOUR_PACK, submission.eav.act_fpd)
            stock_report.add_product_stock(config.Products.TWENTY_FOUR_PACK, submission.eav.act_fps)
            stock_report.save()
        elif submission.xform.keyword == stock_reports[1]:
            required_length = len(config.Products.QUN_REPORT) * 2
            if values_count != required_length:
                if values_count < required_length:
                    submission.response = "This is an incomplete report. Please submit ALL of your QUN stock data in the form 'qun 1 2 3 4'"
                submission.has_errors = True
                submission.save()
                return
            stock_report = ProductReportsHelper(health_provider.facility.supply_point,
                                                const.Reports.SOH,
                                                submission.message)
    
            stock_report.add_product_receipt(config.Products.OTHER_ACT_STOCK, submission.eav.qun_oad)
            stock_report.add_product_stock(config.Products.OTHER_ACT_STOCK, submission.eav.qun_oas)
            stock_report.add_product_receipt(config.Products.QUININE, submission.eav.qun_qud)
            stock_report.add_product_stock(config.Products.QUININE, submission.eav.qun_qus)
            stock_report.save()
    
        elif submission.xform.keyword == stock_reports[2]:
            required_length = len(config.Products.RDT_REPORT) * 2
            if values_count != required_length:
                if values_count < required_length:
                    submission.response = "This is an incomplete report. Please submit ALL of your RDT stock data in the form 'act 1 2'"
                submission.has_errors = True
                submission.save()
                return
            stock_report = ProductReportsHelper(health_provider.facility.supply_point,
                                                const.Reports.SOH,
                                                submission.message)
    
            stock_report.add_product_receipt(config.Products.RAPID_DIAGNOSTIC_TEST, submission.eav.rdt_rdd)
            stock_report.add_product_stock(config.Products.RAPID_DIAGNOSTIC_TEST, submission.eav.rdt_rds)
            stock_report.save()
    except Exception, e:
        if submission.xform.keyword in stock_reports:
            submission.response = unicode(e)
            submission.has_errors = True
            submission.save()
        return
    return

xform_received.connect(xform_received_handler, weak=True)

def update_supply_point_from_facility(sender, instance, **kwargs):
    """ 
    whenever a facility is updated, automatically update the supply point
    """
    try:
        supply_point = instance.supply_point
    except SupplyPoint.DoesNotExist:
        supply_point = None
    try:
        base = HealthFacilityBase.objects.get(pk=instance.pk)
    except HealthFacilityBase.DoesNotExist:
        base = instance
    if supply_point is None:
        # create
        try:
            instance.supply_point = create_supply_point_from_facility(base)
        except ValueError:
            logging.error('facility %s has no location' % base.pk)
        return

    # else update
    supply_point.set_type_from_string(base.type.slug)
    try:
        supply_point.location = get_location_from_facility(base)
    except ValueError:
        logging.error('facility %s has no location' & base.pk)
    supply_point.save()
    return

post_save.connect(update_supply_point_from_facility, HealthFacility)
