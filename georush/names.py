"""Viewer-facing country names. Catalog data, answer checks and history keep the verified upstream names."""

# Shorter, more familiar English names for the video screens only. Every key is an exact upstream name;
# every value is unique among the 190 catalog names (checked by tests).
DISPLAY_NAMES = {
    'United States of America': 'United States',
    'Czech Republic': 'Czechia',
    'Brunei Darussalam': 'Brunei',
    'Federated States of Micronesia': 'Micronesia',
    'Democratic Republic of the Congo': 'DR Congo',
    "Côte d'Ivoire": 'Ivory Coast',
    'Cabo Verde': 'Cape Verde',
    'Türkiye': 'Turkey',
}


def display_name(name):
    return DISPLAY_NAMES.get(name, name)
