from django import template
from leads.models import CaseField, CaseValue
from datetime import date, datetime

register = template.Library()

@register.filter
def get_field_value(instance, field_name):
    # First, try to get the attribute from the Lead instance
    value = getattr(instance, field_name, None)
    
    if value is not None:
        if isinstance(value, datetime):
            value = value.date()
        if field_name == "commission":
            value = str(value) + "%"
        if field_name == "co_commission":
            value = str(value) + "%"
        if field_name == "description":
            if len(value) > 20:
                value = value[:20]+"..."
        return value
    
    if field_name == "Order-ID":
        # Assuming 'created_at' is the field storing the creation date
        created_date = instance.date_added.date()
        same_day_leads = instance.__class__.objects.filter(date_added__date=created_date).order_by('date_added')
        
        # Get the index of the current instance in the list of same-day leads (1-based)
        lead_index = list(same_day_leads).index(instance) + 1
        
        # Format the Order-ID: SEIYYMMDD00X
        company_abbreviation = "SEI"
        order_id = f"{company_abbreviation}{created_date.strftime('%y%m%d')}{lead_index:03d}"
        return order_id
    # If the attribute is not found, try to get it from CaseValue
    try:
        # Get the CaseField that matches the field_name for the user's profile
        case_field = CaseField.objects.get(name=field_name, user=instance.organisation)
        # Get the CaseValue for this field and lead
        case_value = CaseValue.objects.get(lead=instance, field=case_field)
        
        # Return the appropriate value based on the field type
        if case_field.field_type == 'text':
            return case_value.value_text
        elif case_field.field_type == 'number':
            return case_value.value_number
        elif case_field.field_type == 'date':
            return case_value.value_date
    except (CaseField.DoesNotExist, CaseValue.DoesNotExist):
        return None

    return None