from geolocation_in_aws import Geolocation
from plot_map import MapBuilder

from common import cdgeb_probes, cdgeb_frontends, cdgeb_files
from common import probeId2Name, frontendId2Name, fileId2Name
from common import frontend_locations, real_fe_for_file, real_file_for_fe
from common import aws_distances, aws_delays


def test_for_server(frontend):
    filename = real_file_for_fe[frontend]
    delays_from_server = {frontend_name:aws_delays[(frontend_name, filename_d)] for (frontend_name, filename_d) in aws_delays.keys() \
                        if filename_d == filename}
    delays_from_server.pop(frontend)    
    
    target = Geolocation.geolocate_target(delays_from_server, frontend_locations)
    # print('Estimation of server', frontend, 'is', target)
    
    closest = Geolocation.closest_frontend(target, frontend_locations)
    # print('Closest server to estimation:', closest)
    
    map = MapBuilder(f'{frontend}_estimated')
    map.add_frontends()
    map.add_point(target, f'estimated-location-of-{frontend}')
    map.add_circle(target, Geolocation.haversine(target, frontend_locations[frontend]))
    map.save_map()

    return closest

if __name__ == '__main__':
    results = dict()
    for frontend in cdgeb_frontends:
        closest = test_for_server(frontend)
        results[frontend] = closest

    [print(k, ":", k == v, ", error (km): ", round(Geolocation.haversine(frontend_locations[k], frontend_locations[v]), 2), 
           f'[{v}]') \
     for k,v in results.items()]
