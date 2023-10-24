from django.template.defaulttags import register


@register.filter
def get_dict_item_by_key(key, result_dict):
    return result_dict.get(key, "")
