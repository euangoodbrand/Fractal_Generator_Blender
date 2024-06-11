bl_info = {
    "name": "Fractal Generator",
    "author": "Euan Goodbrand",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Tools > Fractal Generator",
    "description": "Generate fractal structures",
    "category": "Add Mesh",
}

import bpy
import math
import mathutils

# ------------------ Script Functions ------------------

def rotate_object(obj, angle, axis):
    mat_rot = mathutils.Matrix.Rotation(angle, 4, axis)
    obj.data.transform(mat_rot)
    obj.data.update()
    
def add_camera_and_zoom_animation(location, end_frame):
    # Add a camera
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    
    # Set the location and rotation properties for the camera
    camera.location = (1.66, -8, 4)
    
    # Rotate the camera
    camera.rotation_euler[0] = math.radians(74)
    camera.rotation_euler[1] = 0
    camera.rotation_euler[2] = 0
    
    # Set the starting location for the animation
    camera.keyframe_insert(data_path="location", frame=1)
    
    # Set the ending location for the animation
    camera.keyframe_insert(data_path="location", frame=end_frame)

def add_floor_and_backdrop(size):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = 'Floor'
    
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, size / 2, size / 4))
    backdrop = bpy.context.object
    backdrop.name = 'Backdrop'
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.rotate(value=-math.pi / 2, orient_axis='X')
    bpy.ops.object.mode_set(mode='OBJECT')

def add_lighting():
    bpy.ops.object.light_add(type='SUN', location=(10, -10, 10))
    bpy.ops.object.light_add(type='POINT', location=(10, -10, 10))
    bpy.ops.object.light_add(type='POINT', location=(-10, -10, 10))
    bpy.ops.object.light_add(type='POINT', location=(10, 10, 10))
    bpy.ops.object.light_add(type='POINT', location=(-10, 10, 10))

def sierpinski_3d(base_triangle, location, size, iterations):
    if iterations == 0:
        instance = bpy.data.objects.new(name="Triangle_Instance_3D", object_data=base_triangle.data)
        bpy.context.collection.objects.link(instance)
        instance.location = location
        instance.scale = (size, size, size)
        return

    s = size / 2.0
    sierpinski_3d(base_triangle, (location[0], location[1], location[2]), s, iterations - 1)
    sierpinski_3d(base_triangle, (location[0] + s, location[1], location[2]), s, iterations - 1)
    sierpinski_3d(base_triangle, (location[0] + 0.5*s, location[1] + math.sqrt(3)*0.5*s, location[2]), s, iterations - 1)
    sierpinski_3d(base_triangle, (location[0] + 0.5*s, location[1] + math.sqrt(3)*0.5*s/3, location[2] + math.sqrt(6)/3.0*s), s, iterations - 1)  

def assign_material_to_fractal(color):
    mat = bpy.data.materials.new(name="Fractal_Material")
    mat.diffuse_color = (color[0], color[1], color[2], 1.0)  # Correct format
    mat.specular_intensity = 0.5
    for obj in bpy.data.objects:
        if "Triangle_Instance_3D" in obj.name:
            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat


# ------------------ End of Script Functions ------------------

# Properties for the UI
class FractalProperties(bpy.types.PropertyGroup):
    fractal_type: bpy.props.EnumProperty(
        name="Type",
        description="Type of Fractal",
        items=[("SIERPINSKI", "Sierpinski Tetrahedron", "")],
        default="SIERPINSKI"
    )
    recursion_level: bpy.props.IntProperty(
        name="Recursion Level",
        description="Number of recursive steps",
        default=5,
        min=1,
        max=10
    )
    material_color: bpy.props.FloatVectorProperty(
        name="Material Color",
        description="Color for the fractal",
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0, max=1.0
    )

# Operator for the button in the UI
class OBJECT_OT_generate_fractal(bpy.types.Operator):
    bl_idname = "object.generate_fractal"
    bl_label = "Generate Fractal"
    bl_description = "Generate the fractal"

    def execute(self, context):
        # Clear the scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        # Create the base triangle
        vertices = [(0, -1 / math.sqrt(3), 0),
                    (0.5, 1 / (2 * math.sqrt(3)), 0),
                    (-0.5, 1 / (2 * math.sqrt(3)), 0),
                    (0, 0, math.sqrt(2 / 3))]

        edges = []
        faces = [(0, 1, 2), (0, 1, 3), (1, 2, 3), (2, 0, 3)]

        mesh_data = bpy.data.meshes.new("base_mesh_data")
        mesh_data.from_pydata(vertices, edges, faces)
        base_triangle_3d = bpy.data.objects.new("base_object_data", mesh_data)
        bpy.context.collection.objects.link(base_triangle_3d)
        
        # Rotate base triangle
        rotate_object(base_triangle_3d, math.pi, 'Z')
        
        # Generate the fractal
        number_of_refractions = context.scene.fractal_props.recursion_level
        sierpinski_3d(base_triangle_3d, (0, 0, 0), 4, number_of_refractions)
        
        # Add floor, backdrop, and lighting
        add_floor_and_backdrop(100)
        add_lighting()
        
        # Hide base triangle
        base_triangle_3d.hide_viewport = True
        base_triangle_3d.hide_render = True
        
        # Assign material
        material_color = context.scene.fractal_props.material_color
        assign_material_to_fractal(material_color)
        
        # Add a camera and animate a zoom towards the fractal over 100 frames
        add_camera_and_zoom_animation((1.66, -8, 4), 100)

        return {'FINISHED'}

# UI Panel
class OBJECT_PT_fractal_panel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_fractal_panel"
    bl_label = "Fractal Generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        fractal_props = scene.fractal_props

        layout.prop(fractal_props, "fractal_type")
        layout.prop(fractal_props, "recursion_level")
        layout.prop(fractal_props, "material_color")

        layout.operator("object.generate_fractal")

# Register classes and properties with Blender
classes = (FractalProperties, OBJECT_OT_generate_fractal, OBJECT_PT_fractal_panel)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.fractal_props = bpy.props.PointerProperty(type=FractalProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
    del bpy.types.Scene.fractal_props

if __name__ == "__main__":
    register()
