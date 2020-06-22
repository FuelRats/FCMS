import argparse
import sys

from pyramid.paster import bootstrap, setup_logging
from sqlalchemy.exc import OperationalError

from .. import models


def register_regions(dbsession):
    """
    Add or update models / fixtures in the database.

    """
    regions = [
        'Galactic Centre',
        'Empyrean Straits',
        'Ryker\'s Hope',
        'Odin\'s Hold',
        'Norma Arm',
        'Arcadian Stream',
        'Izanami',
        'Inner Orion - Perseus Conflux',
        'Inner Scutum - Centaurus Arm',
        'Norma Expanse',
        'Trojan Belt',
        'The Veils',
        'Newton\'s Vault',
        'The Conduit',
        'Outer Orion - Perseus Conflux',
        'Orion - Cygnus Arm',
        'Temple',
        'Inner Orion Spur',
        'Hawking\'s Gap',
        'Dryman\'s Point',
        'Sagittarius - Carina Arm',
        'Mare Somnia',
        'Acheron',
        'Formorian Frontier',
        'Hieronymus Delta',
        'Outer Scutum - Centaurus Arm',
        'Outer Arm',
        'Aquila\'s Halo',
        'Errant Marches',
        'Perseus Arm',
        'Formidine Rift',
        'Vulcan Gate',
        'Elysian Shore',
        'Sanguineous Rim',
        'Outer Orion Spur',
        'Achilles\'s Altar',
        'Xibalba',
        'Lyra\'s Song',
        'Tenebrae',
        'The Abyss',
        'Kepler\'s Crest',
        'The Void'
    ]

    pois = [
        'The Bubble',
        'Colonia',
        'Beagle Point',
        'Sagittarius A*'
    ]

    for region in regions:
        reg = models.routes.Region(name=region, isPOI=False)
        dbsession.add(reg)

    for poi in pois:
        reg = models.routes.Region(name=poi, isPOI=True)
        dbsession.add(reg)


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config_uri',
        help='Configuration file, e.g., development.ini',
    )
    return parser.parse_args(argv[1:])


def main(argv=sys.argv):
    args = parse_args(argv)
    setup_logging(args.config_uri)
    env = bootstrap(args.config_uri)

    try:
        with env['request'].tm:
            dbsession = env['request'].dbsession
            register_regions(dbsession)
    except OperationalError:
        print('''
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to initialize your database tables with `alembic`.
    Check your README.txt for description and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.
            ''')
