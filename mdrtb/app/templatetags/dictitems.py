from django.template.defaulttags import register


@register.filter
def get_dict_item_by_key(result_dict):
    print(result_dict)
