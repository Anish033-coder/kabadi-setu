"""Small human questions for labels that cannot establish a catalogue item."""
OPTIONS = {
    'bottle': ('pet-bottle', 'glass-bottle'),
    'container': ('rigid-plastic', 'glass-bottle'),
    'can': ('aluminium-can',),
}


def options_for(kind, catalogue):
    allowed = {item['id'] for item in catalogue['items']}
    return [item for item in OPTIONS.get(kind, ()) if item in allowed]


def question_for(names):
    bottle = bool(names & {'bottle', 'beer bottle', 'water bottle', 'wine bottle', 'pop bottle'})
    can = bool(names & {'can', 'tin'})
    # Bottle + Jar commonly describe one container. A can as well is ambiguous.
    if can and (bottle or 'jar' in names):
        return None
    if bottle:
        return 'bottle'
    if can:
        return 'can'
    if 'jar' in names:
        return 'container'
    return None
