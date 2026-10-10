"""Short human choices for labels that name a kind of thing but not the catalogue item."""
# Each family lists the catalogue items its broad labels are consistent with. Code ranks
# the shortlist; the person chooses one or searches. Extend only after reviewing dev photos.
FAMILIES = (
    ('paper', {'paper', 'text', 'document', 'book', 'publication', 'page', 'poster', 'advertisement',
               'flyer', 'brochure', 'magazine', 'receipt', 'letter', 'envelope'},
     ('newspaper', 'notebooks', 'office-paper', 'cardboard')),
    ('box', {'box', 'carton', 'package'}, ('cardboard',)),
    ('bottle', {'bottle', 'beer bottle', 'water bottle', 'wine bottle', 'pop bottle'}, ('pet-bottle', 'glass-bottle')),
    ('plastic', {'plastic'}, ('pet-bottle', 'rigid-plastic')),
    ('can', {'can', 'tin'}, ('aluminium-can',)),
    ('container', {'jar', 'cookware', 'pot', 'bucket', 'container', 'tupperware'},
     ('rigid-plastic', 'steel-utensil', 'glass-bottle')),
    ('metal', {'aluminium', 'metal', 'steel', 'stainless steel', 'cookware', 'pot', 'cutlery', 'spoon'},
     ('steel-utensil', 'aluminium-can')),
    ('electronics', {'electronics', 'remote control', 'cable', 'wire', 'adapter', 'plug', 'hardware',
                     'computer hardware', 'headphones', 'monitor', 'keyboard', 'mouse'}, ('electronics',)),
)
MAX_CHOICES = 4


def options_for(options, catalogue):
    allowed = {item['id'] for item in catalogue['items']}
    return [item for item in options or () if item in allowed][:MAX_CHOICES]


def shortlist(names, catalogue, specific=()):
    """Rank items by how many label families agree; specific matches first. Returns (kind, options)."""
    scores = {item: 2 for item in specific}
    kind = 'items' if specific else None
    for family, labels, items in FAMILIES:
        if names & labels:
            kind = kind or family
            for item in items:
                scores[item] = scores.get(item, 0) + 1
    # sorted() is stable, so ties keep family order.
    options = options_for(sorted(scores, key=lambda item: -scores[item]), catalogue)
    return (kind, tuple(options)) if options else (None, ())
