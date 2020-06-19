import transaction
import re


from sqlalchemy.exc import DataError, IntegrityError

from FCMS.models import (
    Market, Carrier
)


carrier_rs = '^[A-Za-z0-9]{3}-[A-Za-z0-9]{3}$'
carrier_r = re.compile(carrier_rs)


def process_eddn(session, data):
    new_carriers = 0
    new_commodities = 0
    updated_carriers = 0
    if 'commodities' in data and carrier_r.search(data['stationName']):

        oc = session.query(Carrier).filter(Carrier.callsign == data['stationName']).one_or_none()
        if oc:
            session.query(Market).filter(Market.carrier_id == oc.id).delete()
            for commodity in data['commodities']:
                nc = Market(carrier_id=oc.id, commodity_id=0, name=commodity['name'], stock=commodity['stock'],
                            buyPrice=commodity['buyPrice'], sellPrice=commodity['sellPrice'], demand=commodity['demand'])
                session.add(nc)
                new_commodities = new_commodities+1
            transaction.commit()

        else:
            newcarrier = Carrier(callsign=data['stationName'],
                                 name="Unknown Name", lastUpdated=data['timestamp'],
                                 currentStarSystem=data['systemName'],
                                 hasShipyard=False,
                                 hasOutfitting=False,
                                 hasCommodities=False,
                                 hasRefuel=False,
                                 hasRepair=False,
                                 hasRearm=False,
                                 trackedOnly=True,
                                 )
            session.add(newcarrier)
            session.flush()
            session.refresh(newcarrier)
            new_carriers = new_carriers + 1
            for commodity in data['commodities']:
                nc = Market(carrier_id=newcarrier.id, commodity_id=0, name=commodity['name'], stock=commodity['stock'],
                            buyPrice=commodity['buyPrice'], sellPrice=commodity['sellPrice'],
                            demand=commodity['demand'])
                session.add(nc)
                new_commodities = new_commodities + 1
            session.flush()
    if 'event' in data:
        if data['event'] in {'Docked', 'CarrierJump'} and data['StationType'] == 'FleetCarrier':
            try:
                print(f"Dock event for {data['StationName']} in {data['StarSystem']}")
                oldcarrier = session.query(Carrier).filter(Carrier.callsign == data['StationName'])
                if oldcarrier:
                    oldcarrier.currentStarSystem = data['StarSystem']
                    oldcarrier.hasShipyard = True if 'shipyard' in data['StationServices'] else False
                    oldcarrier.hasOutfitting = True if 'outfitting' in data[
                        'StationServices'] else False
                    oldcarrier.hasCommodities = True if 'commodities' in data[
                        'StationServices'] else False
                    oldcarrier.hasRefuel = True if 'refuel' in data['StationServices'] else False
                    oldcarrier.hasRepair = True if 'repair' in data['StationServices'] else False
                    oldcarrier.hasRearm = True if 'rearm' in data['StationServices'] else False
                    oldcarrier.lastUpdated = data['timestamp']
                    oldcarrier.x = data['StarPos'][0]
                    oldcarrier.y = data['StarPos'][1]
                    oldcarrier.z = data['StarPos'][2]
                    updated_carriers = updated_carriers + 1
                else:
                    newcarrier = Carrier(callsign=data['StationName'],
                                         name="Unknown Name", lastUpdated=data['timestamp'],
                                         currentStarSystem=data['StarSystem'],
                                         hasShipyard=True if 'shipyard' in data['StationServices']
                                         else False,
                                         hasOutfitting=True if 'outfitting' in data['StationServices']
                                         else False,
                                         hasCommodities=True if 'commodities' in data['StationServices']
                                         else False,
                                         hasRefuel=True if 'refuel' in data['StationServices'] else False,
                                         hasRepair=True if 'repair' in data['StationServices'] else False,
                                         hasRearm=True if 'rearm' in data['StationServices'] else False,
                                         trackedOnly=True,
                                         x=data['StarPos'][0],
                                         y=data['StarPos'][1],
                                         z=data['StarPos'][2]
                                         )
                    session.add(newcarrier)
                    new_carriers = new_carriers + 1
                transaction.commit()
            except DataError:
                transaction.abort()
    return {'new_commodities': new_commodities, 'updated_carriers': updated_carriers, 'new_carriers': new_carriers}

