from entities.base import Entity
import numpy as np

class Cube(Entity):
    """
        A basic object in the world, with a position and rotation.
    """
    __slots__ = tuple()


    def __init__(self, position: list[float], eulers: list[float]):
        """
            Initialize the cube.

            Parameters:

                position: the position of the entity.

                eulers: the rotation of the entity
                        about each axis.
        """

        super().__init__(position, eulers)
    
    def update(self, dt: float, camera_pos: np.ndarray) -> None:
        """
            Update the cube.

            Parameters:

                dt: framerate correction factor.

                camera_pos: the position of the camera in the scene
        """

        self.eulers[2] += 0.25 * dt
        
        if self.eulers[2] > 360:
            self.eulers[2] -= 360