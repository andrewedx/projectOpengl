from OpenGL.GL import *
import numpy as np
import pyrr

from core.constants import *
from graphics.shader import Shader
from graphics.mesh import *
from graphics.material import Material
from graphics.skybox import Skybox
from core.scene import Camera
from entities.pointlight import PointLight
from entities.base import Entity
from utils.colors import *

class GraphicsEngine:
    """
        Draws entities and stuff.
    """
    __slots__ = ("meshes", "materials", "shaders", "skybox_mesh", "skybox_shader", "skybox", "shadow_fbo", "shadow_depth_texture", "shadow_width", "shadow_height", "shadows_enabled", "window_width", "window_height")

    def __init__(self):
        """
            Initializes the rendering system.
        """

        self.window_width = SCREEN_WIDTH
        self.window_height = SCREEN_HEIGHT

        self._set_up_opengl()

        self._create_assets()

        self._set_onetime_uniforms()

        self._get_uniform_locations()

        self._create_shadow_map()

        self.shadows_enabled = True

        ## set up skybox
        self.skybox_mesh = SkyboxMesh()
        self.skybox_shader = Shader("shaders/skybox_vertex.txt", "shaders/skybox_fragment.txt")
        self.skybox = Skybox([
            "gfx/texture.png",
            "gfx/texture.png",
            "gfx/texture.png",
            "gfx/texture.png",
            "gfx/texture.png",
            "gfx/texture.png"
        ])
    
    def _set_up_opengl(self) -> None:
        """
            Configure any desired OpenGL options
        """
        r,g,b = hex_to_rgb("#028058")
        print(r,g,b)
        glClearColor(r, g, b, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # glEnable(GL_CULL_FACE)
        # glCullFace(GL_BACK)

    def _create_assets(self) -> None:
        """
            Create all of the assets needed for drawing.
        """

        # monkey_model = ObjMesh("models/monkeyTextured.obj")
        

        self.meshes: dict[int, Mesh] = {
            # ENTITY_TYPE["CUBE"]: monkey_model,
            ENTITY_TYPE["MEDKIT"]: RectMesh(w = 0.6, h = 0.5),
            ENTITY_TYPE["POINTLIGHT"]: RectMesh(w = 0.2, h = 0.1),
        }
        self.meshes[ENTITY_TYPE["CUBE"]] = MultiMaterialMesh("models/assembler.obj")

        self.materials: dict[int, Material] = {
            # ENTITY_TYPE["CUBE"]: Material(monkey_model.texture_path),
            ENTITY_TYPE["MEDKIT"]: Material("gfx/medkit.png"),
            ENTITY_TYPE["POINTLIGHT"]: Material("gfx/Light-bulb.png"),
        }
        
        self.shaders: dict[int, Shader] = {
            PIPELINE_TYPE["STANDARD"]: Shader(
                "shaders/vertex.txt", "shaders/fragment.txt"),
            PIPELINE_TYPE["EMISSIVE"]: Shader(
                "shaders/vertex_light.txt", "shaders/fragment_light.txt"),
            PIPELINE_TYPE["SHADOW"]: Shader(
                "shaders/shadow_vertex.txt", "shaders/shadow_fragment.txt")
        }
    
    def _set_onetime_uniforms(self) -> None:
        """
            Some shader data only needs to be set once.
        """

        ratio = self.window_width / self.window_height
        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy=45, aspect=ratio, near=0.1, far=1000, dtype=np.float32
        )

        for shader in self.shaders.values():
            shader.use()
            glUniform1i(glGetUniformLocation(shader.program, "imageTexture"), 0)

            glUniformMatrix4fv(
                glGetUniformLocation(shader.program,"projection"),
                1, GL_FALSE, projection_transform
            )

    def _get_uniform_locations(self) -> None:
        """
            Query and store the locations of shader uniforms
        """

        shader = self.shaders[PIPELINE_TYPE["STANDARD"]]
        shader.use()

        shader.cache_single_location(
            UNIFORM_TYPE["CAMERA_POS"], "cameraPosition")
        shader.cache_single_location(UNIFORM_TYPE["MODEL"], "model")
        shader.cache_single_location(UNIFORM_TYPE["VIEW"], "view")

        for i in range(8):

            shader.cache_multi_location(
                UNIFORM_TYPE["LIGHT_COLOR"], f"Lights[{i}].color")
            shader.cache_multi_location(
                UNIFORM_TYPE["LIGHT_POS"], f"Lights[{i}].position")
            shader.cache_multi_location(
                UNIFORM_TYPE["LIGHT_STRENGTH"], f"Lights[{i}].strength")
        
        shader = self.shaders[PIPELINE_TYPE["EMISSIVE"]]
        shader.use()

        shader.cache_single_location(UNIFORM_TYPE["MODEL"], "model")
        shader.cache_single_location(UNIFORM_TYPE["VIEW"], "view")
        shader.cache_single_location(UNIFORM_TYPE["TINT"], "tint")

        shader = self.shaders[PIPELINE_TYPE["SHADOW"]]
        shader.use()

        shader.cache_single_location(UNIFORM_TYPE["MODEL"], "model")
        shader.cache_single_location(UNIFORM_TYPE["LIGHT_MATRIX"], "lightSpaceMatrix")


    
    def _create_shadow_map(self):
        self.shadow_width = 1024
        self.shadow_height = 1024

        # Generate framebuffer
        self.shadow_fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)

        # Generate depth texture
        self.shadow_depth_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.shadow_depth_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT,
                    self.shadow_width, self.shadow_height, 0,
                    GL_DEPTH_COMPONENT, GL_FLOAT, None)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)

        border_color = [1.0, 1.0, 1.0, 1.0]
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, border_color)

        # Attach depth texture to framebuffer
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                            GL_TEXTURE_2D, self.shadow_depth_texture, 0)

        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)

        # Unbind framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _get_light_space_matrix(self, light_pos: np.ndarray) -> np.ndarray:
        light_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)  # look at origin
        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        light_view = pyrr.matrix44.create_look_at(
            eye=light_pos, target=light_target, up=up, dtype=np.float32
        )

        # Orthographic projection for directional light
        light_proj = pyrr.matrix44.create_orthogonal_projection(
            -20, 20,   # X range
            -20, 20,   # Y range
            0.1, 50.0  # Z near/far (in light space)
)

        return pyrr.matrix44.multiply(light_view, light_proj)
    
    def _update_projection_matrices(self) -> None:
        aspect = self.window_width / self.window_height
        projection = pyrr.matrix44.create_perspective_projection(
            fovy=45, aspect=aspect, near=0.1, far=1000, dtype=np.float32
        )
        for shader in self.shaders.values():
            shader.use()
            loc = glGetUniformLocation(shader.program, "projection")
            if loc != -1:  # Only update if the shader uses this uniform
                glUniformMatrix4fv(loc, 1, GL_FALSE, projection)



    def _recreate_shadow_map(self, width: int, height: int) -> None:
        # Delete old framebuffer and texture
        glDeleteFramebuffers(1, [self.shadow_fbo])
        glDeleteTextures(1, [self.shadow_depth_texture])

        self.shadow_width = width
        self.shadow_height = height

        # Generate framebuffer
        self.shadow_fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)

        # Generate depth texture
        self.shadow_depth_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.shadow_depth_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT,
                    self.shadow_width, self.shadow_height, 0,
                    GL_DEPTH_COMPONENT, GL_FLOAT, None)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)

        border_color = [1.0, 1.0, 1.0, 1.0]
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, border_color)

        # Attach depth texture to framebuffer
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                            GL_TEXTURE_2D, self.shadow_depth_texture, 0)

        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)

        # Unbind framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def resize(self, width: int, height: int) -> None:
        self.window_width = width
        self.window_height = height
        self._update_projection_matrices()
        self._recreate_shadow_map(width, height)
    
    def render(self, 
        camera: Camera, 
        renderables: dict[int, list[Entity]],
        lights: list[PointLight]) -> None:
        """
            Draw everything.

            Parameters:
                camera: the scene's camera
                renderables: all the entities to draw
                lights: all the lights in the scene
        """
        if self.shadows_enabled:
            # STEP 1: Render shadow map
            glViewport(0, 0, self.shadow_width, self.shadow_height)
            glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
            glClear(GL_DEPTH_BUFFER_BIT)

            shadow_shader = self.shaders[PIPELINE_TYPE["SHADOW"]]
            shadow_shader.use()
            glUniform1i(glGetUniformLocation(shadow_shader.program, "shadowsEnabled"), int(self.shadows_enabled))

            light_pos = lights[0].position  # Use the first light
            light_space_matrix = self._get_light_space_matrix(light_pos)

            glUniformMatrix4fv(
                shadow_shader.fetch_single_location(UNIFORM_TYPE["LIGHT_MATRIX"]),
                1, GL_FALSE, light_space_matrix
            )

            for entity_type, entities in renderables.items():
                mesh = self.meshes[entity_type]
                if isinstance(mesh, MultiMaterialMesh):
                    for entity in entities:
                        glUniformMatrix4fv(
                            shadow_shader.fetch_single_location(UNIFORM_TYPE["MODEL"]),
                            1, GL_FALSE, entity.get_model_transform()
                        )
                        mesh.render()
                else:
                    mesh.arm_for_drawing()
                    for entity in entities:
                        glUniformMatrix4fv(
                            shadow_shader.fetch_single_location(UNIFORM_TYPE["MODEL"]),
                            1, GL_FALSE, entity.get_model_transform()
                        )
                        mesh.draw()

            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            glViewport(0, 0, self.window_width, self.window_height)

        else:
            light_space_matrix = np.identity(4, dtype=np.float32)

        # STEP 2: Main geometry render
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        view = camera.get_view_transform()
        shader = self.shaders[PIPELINE_TYPE["STANDARD"]]
        shader.use()
        glUniform1i(glGetUniformLocation(shader.program, "shadowsEnabled"), int(self.shadows_enabled))


        # Pass light-space matrix and shadow map
        glUniformMatrix4fv(
            glGetUniformLocation(shader.program, "lightSpaceMatrix"),
            1, GL_FALSE, light_space_matrix
        )

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.shadow_depth_texture)
        glUniform1i(glGetUniformLocation(shader.program, "shadowMap"), 1)

        glUniformMatrix4fv(
            shader.fetch_single_location(UNIFORM_TYPE["VIEW"]),
            1, GL_FALSE, view
        )
        glUniform3fv(
            shader.fetch_single_location(UNIFORM_TYPE["CAMERA_POS"]),
            1, camera.position
        )

        for i, light in enumerate(lights):
            glUniform3fv(shader.fetch_multi_location(UNIFORM_TYPE["LIGHT_POS"], i), 1, light.position)
            glUniform3fv(shader.fetch_multi_location(UNIFORM_TYPE["LIGHT_COLOR"], i), 1, light.color)
            glUniform1f(shader.fetch_multi_location(UNIFORM_TYPE["LIGHT_STRENGTH"], i), light.strength)

        for entity_type, entities in renderables.items():
            mesh = self.meshes[entity_type]
            if isinstance(mesh, MultiMaterialMesh):
                for entity in entities:
                    glUniformMatrix4fv(
                        shader.fetch_single_location(UNIFORM_TYPE["MODEL"]),
                        1, GL_FALSE, entity.get_model_transform()
                    )
                    mesh.render()
            else:
                if entity_type not in self.materials:
                    continue
                self.materials[entity_type].use()
                mesh.arm_for_drawing()
                for entity in entities:
                    glUniformMatrix4fv(
                        shader.fetch_single_location(UNIFORM_TYPE["MODEL"]),
                        1, GL_FALSE, entity.get_model_transform()
                    )
                    mesh.draw()

        # STEP 3: Emissive objects (e.g., point lights)
        emissive_shader = self.shaders[PIPELINE_TYPE["EMISSIVE"]]
        emissive_shader.use()
        glUniformMatrix4fv(
            emissive_shader.fetch_single_location(UNIFORM_TYPE["VIEW"]),
            1, GL_FALSE, view
        )

        material = self.materials[ENTITY_TYPE["POINTLIGHT"]]
        mesh = self.meshes[ENTITY_TYPE["POINTLIGHT"]]
        material.use()
        mesh.arm_for_drawing()
        for light in lights:
            glUniform3fv(
                emissive_shader.fetch_single_location(UNIFORM_TYPE["TINT"]), 
                1, light.color
            )
            glUniformMatrix4fv(
                emissive_shader.fetch_single_location(UNIFORM_TYPE["MODEL"]),
                1, GL_FALSE, light.get_model_transform()
            )
            mesh.draw()

        # STEP 4: Draw skybox
        glDepthFunc(GL_LEQUAL)
        self.skybox_shader.use()

        skybox_view = pyrr.matrix44.create_from_matrix33(
            pyrr.matrix33.create_from_matrix44(view)
        )
        aspect = self.window_width / self.window_height
        projection = pyrr.matrix44.create_perspective_projection(
            fovy=45, aspect=aspect, near=0.1, far=1000
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.skybox_shader.program, "view"),
            1, GL_FALSE, skybox_view
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.skybox_shader.program, "projection"),
            1, GL_FALSE, projection
        )

        self.skybox.use()
        self.skybox_mesh.arm_for_drawing()
        self.skybox_mesh.draw()
        glDepthFunc(GL_LESS)

        glFlush()

    def toggle_shadows(self):
        self.shadows_enabled = not self.shadows_enabled
        print("Shadows enabled:", self.shadows_enabled)

    def reload_shaders(self):
        print("Reloading shaders...")

        # Destroy old programs
        for shader in self.shaders.values():
            shader.destroy()

        # Rebuild everything
        self._create_assets()
        self._get_uniform_locations()
        self._set_onetime_uniforms()


    def destroy(self) -> None:
        """ free any allocated memory """

        for mesh in self.meshes.values():
            mesh.destroy()
        for material in self.materials.values():
            material.destroy()
        for shader in self.shaders.values():
            shader.destroy()

        glDeleteFramebuffers(1, [self.shadow_fbo])
        glDeleteTextures(1, [self.shadow_depth_texture])
        self.skybox.destroy()
        self.skybox_mesh.destroy()
        self.skybox_shader.destroy()
