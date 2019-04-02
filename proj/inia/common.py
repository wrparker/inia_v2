import tempfile
import csv
from .models import SavedSearch

def open_tmp_search(id):
    try:
        search = SavedSearch.objects.get(pk=id)
        inputs = search.search_parameters
    except:
        return {}
    inputs['id'] = search.id
    return inputs


def dict_list_to_csv(dict_list):
    '''
    :param dict_list: A list of dictionaries
    :return: None if invalid input, file location if valid.
    '''
    if len(dict_list) < 1:
        return None
    keys = dict_list[0].keys()
    tmp_file = tempfile.mkstemp(suffix='.csv', prefix='output')
    with open(tmp_file[1], 'w') as f:
        dict_writer = csv.DictWriter(f,
                                     fieldnames=keys,
                                     quoting=csv.QUOTE_ALL)
        dict_writer.writeheader()
        dict_writer.writerows(dict_list)
    return tmp_file[1]

def color_variant(hex_color, brightness_offset=1):
    """ takes a color like #87c95f and produces a lighter or darker variant """
    if len(hex_color) != 7:
        raise Exception("Passed %s into color_variant(), needs to be in #87c95f format." % hex_color)
    rgb_hex = [hex_color[x:x+2] for x in [1, 3, 5]]
    new_rgb_int = [int(hex_value, 16) + brightness_offset for hex_value in rgb_hex]
    new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int] # make sure new values are between 0 and 255
    # hex() produces "0x88", we want just "88"
    return "#" + "".join([hex(i)[2:] for i in new_rgb_int])
