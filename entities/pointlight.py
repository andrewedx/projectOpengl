from entities.billboard import Billboard
import numpy as np

class PointLight(Billboard):
    """
        A simple pointlight.
    """
    __slots__ = ("color", "strength")


    def __init__(
        self, position: list[float], 
        color: list[float], strength: float):
        """
            Initialize the light.

            Parameters:

                position: position of the light.

                color: (r,g,b) color of the light.

                strength: strength of the light.
        """

        super().__init__(position)
        self.color = np.array(color, dtype=np.float32)
        self.strength = strength
        