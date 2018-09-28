#!/usr/bin/env python

import sys

sys.path.append(
    'PythonAPI/carla-0.9.0-py%d.%d-linux-x86_64.egg' % (sys.version_info.major,
                                                        sys.version_info.minor))


sys.path.append(
    'dist/carla-0.9.0-py%d.%d-linux-x86_64.egg' % (sys.version_info.major,
                                                        sys.version_info.minor))
sys.path.append(
    'PythonAPI/dist/carla-0.9.0-py%d.%d-linux-x86_64.egg' % (sys.version_info.major,
                                                        sys.version_info.minor))

import carla

import os
import random
import time

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')



# This function is here because this functionality haven't been ported to the
# new API yet.
def save_to_disk(image):
    """Save this image to disk (requires PIL installed)."""

    filename = '_images/{:0>6d}_{:s}.png'.format(image.frame_number, image.type)

    try:
        from PIL import Image as PImage
    except ImportError:
        raise RuntimeError(
            'cannot import PIL, make sure pillow package is installed')

    image = PImage.frombytes(
        mode='RGBA',
        size=(image.width, image.height),
        data=image.raw_data,
        decoder_name='raw')
    color = image.split()
    image = PImage.merge("RGB", color[2::-1])


    classes = {
        0: [0, 0, 0],         # None
        1: [70, 70, 70],      # Buildings
        2: [190, 153, 153],   # Fences
        3: [72, 0, 90],       # Other
        4: [220, 20, 60],     # Pedestrians
        5: [153, 153, 153],   # Poles
        6: [157, 234, 50],    # RoadLines
        7: [128, 64, 128],    # Roads
        8: [244, 35, 232],    # Sidewalks
        9: [107, 142, 35],    # Vegetation
        10: [0, 0, 255],      # Vehicles
        11: [102, 102, 156],  # Walls
        12: [220, 220, 0]     # TrafficSigns
    }

    # flatten our data
    # https://stackoverflow.com/a/6501902
    data = np.array(image)
    red, green, blue = data[:,:,0], data[:,:,1], data[:,:,2]

    # find the class that matches this pixel
    for key, value in classes.items():
        mask = (red == key) & (blue == 0) & (green == 0)
        data[:,:,:3][mask] = value

    # transform back into array
    image = PImage.fromarray(data)

    # save to disk
    folder = os.path.dirname(filename)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    image.save(filename)


def main(add_a_camera, enable_autopilot):
    client = carla.Client('localhost', 2000)
    client.set_timeout(2000)

    print('client version: %s' % client.get_client_version())
    print('server version: %s' % client.get_server_version())

    world = client.get_world()

    blueprint_library = world.get_blueprint_library()

    vehicle_blueprints = blueprint_library.filter('vehicle')


    actor_list = []

    try:

        while True:

            bp = random.choice(vehicle_blueprints)

            if bp.contains_attribute('number_of_wheels'):
                n = bp.get_attribute('number_of_wheels')
                print('spawning vehicle %r with %d wheels' % (bp.id, n))

            color = random.choice(bp.get_attribute('color').recommended_values)
            bp.set_attribute('color', color)

            transform = carla.Transform(
                carla.Location(x=180.0, y=199.0, z=40.0),
                carla.Rotation(yaw=0.0))

            vehicle = world.try_spawn_actor(bp, transform)

            if vehicle is None:
                continue
            actor_list.append(vehicle)

            print(vehicle)

            # add to th first vehicle only!!!!!
            if add_a_camera:
                add_a_camera = False
                camera_bp = blueprint_library.find('sensor.camera')
                camera_bp.set_attribute('post_processing', 'SemanticSegmentation')
                camera_transform = carla.Transform(carla.Location(x=0.4, y=0.0, z=2.0))
                camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
                camera.listen(save_to_disk)

            #if enable_autopilot:
            vehicle.set_autopilot(True)
            #else:
            #    vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=-1.0))

            #time.sleep(3)

            #print('vehicle at %s' % vehicle.get_location())
            vehicle.set_location(carla.Location(x=220, y=199, z=38))
            #print('is now at %s' % vehicle.get_location())

            time.sleep(4)

    finally:

        for actor in actor_list:
            actor.destroy()


if __name__ == '__main__':

    main(add_a_camera=True, enable_autopilot=True)
