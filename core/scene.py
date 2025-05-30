import numpy as np
import pyrr
from entities.cube import Cube
from entities.billboard import Billboard
from entities.pointlight import PointLight
from entities.base import Entity
from core.constants import *




class Camera(Entity):
    """
        A first person camera.
    """
    __slots__ = ("forwards", "right", "up")


    def __init__(self, position: list[float]):
        """
            Initialize the camera.

            Parameters:

                position: the camera's position
        """

        super().__init__(position, eulers = [0,0,0])
        self.update(0)
    
    def update(self, dt: float) -> None:
        """
            Update the camera.

            Parameters:

                dt: framerate correction factor
        """

        theta = self.eulers[2]
        phi = self.eulers[1]

        self.forwards = np.array(
            [
                np.cos(np.deg2rad(theta)) * np.cos(np.deg2rad(phi)),
                np.sin(np.deg2rad(theta)) * np.cos(np.deg2rad(phi)),
                np.sin(np.deg2rad(phi))
            ],
            dtype = np.float32
        )

        self.right = np.cross(self.forwards, GLOBAL_Z)

        self.up = np.cross(self.right, self.forwards)

    def get_view_transform(self) -> np.ndarray:
        """
            Returns the camera's world to view
            transformation matrix.
        """

        return pyrr.matrix44.create_look_at(
            eye = self.position,
            target = self.position + self.forwards,
            up = self.up, dtype = np.float32)
    
    def move(self, d_pos) -> None:
        """
            Move by the given amount in the (forwards, right, up) vectors.
        """

        self.position += d_pos[0] * self.forwards \
                        + d_pos[1] * self.right \
                        + d_pos[2] * self.up
    
        #hard coding the z constraint
        # self.position[2] = 2
    
    def spin(self, d_eulers) -> None:
        """
            Spin the camera by the given amount about the (x, y, z) axes.
        """

        self.eulers += d_eulers

        self.eulers[0] %= 360
        self.eulers[1] = min(89, max(-89, self.eulers[1]))
        self.eulers[2] %= 360

class Scene:
    """
        Manages all objects and coordinates their interactions.
    """
    __slots__ = ("entities", "player", "lights")


    def __init__(self):
        """
            Initialize the scene.
        """

        self.entities: dict[int, list[Entity]] = {
            ENTITY_TYPE["CUBE"]: [
                Cube(position = [4,0,0], eulers = [90,0,-90]),
            ],

            ENTITY_TYPE["MEDKIT"]: [
                Billboard(position = [3,0,-0.5])
            ],
        }

        self.lights: list[PointLight] = [
            PointLight(
                position = [1, 1, 1],
                color = [1, 1, 1],
                strength = 2),
            PointLight(
                position = [-10,30,10],
                color = [1.0, 1.0, 1.0],
                strength = 8.0),
            PointLight(
                position = [-10,27,10],
                color = [1.0, 1.0, 1.0],
                strength = 8.0),
            PointLight(
                position = [-10,33,10],
                color = [1.0, 1.0, 1.0],
                strength = 8.0),
            PointLight(
                position = [-14,30,10],
                color = [1.0, 1.0, 1.0],
                strength = 8.0),
            PointLight(
                position = [-14,27,10],
                color = [1.0, 1.0, 1.0],
                strength = 8.0),
            PointLight(
                position = [-14,33,10],
                color = [1.0, 1.0, 1.0],
                strength = 8.0),
        ]

        self.player = Camera(
            position = [0,0,0]
        )

    def update(self, dt: float) -> None:
        """
            Update all objects in the scene.

            Parameters:

                dt: framerate correction factor
        """

        # for entities in self.entities.values():
        #     for entity in entities:
        #         entity.update(dt, self.player.position)
        
        for light in self.lights:
            light.update(dt, self.player.position)

        self.player.update(dt)

    def move_player(self, d_pos: list[float]) -> None:
        """
            move the player by the given amount in the 
            (forwards, right, up) vectors.
        """

        self.player.move(d_pos)
    
    def spin_player(self, d_eulers: list[float]) -> None:
        """
            spin the player by the given amount
            around the (x,y,z) axes
        """

        self.player.spin(d_eulers)
