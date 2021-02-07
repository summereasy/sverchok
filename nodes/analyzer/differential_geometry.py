# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import numpy as np

import bpy
from bpy.props import EnumProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, throttle_and_update_node
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import scipy

operations = [
    ('GRAD', 'Gradient'),
    ('DIV/CURL', 'Divergence and Curl')
    # ('LAPLACE', 'Laplacian Matrix', [('Vertices', 'Polygons')], [('Laplacian Matrix')]),
    # ('MASS', 'Mass Matrix', [('Vertices', 'Polygons')], [('Mass Matrix')])
]

scalar_ops = {'GRAD'}

operation_modes = [(id, name, name, i)
                   for i, (id, name) in enumerate(operations)]

if scipy is None:
    add_dummy('SvDifferentialGeometryNode', "Differential Geometry", 'scipy')
else:
    from scipy.sparse import csr_matrix, spdiags

    class SvDifferentialGeometryNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers:
        Tooltip:
        """

        bl_idname = 'SvDifferentialGeometryNode'
        bl_label = 'Differential Geometry'
        bl_icon = 'FORCE_HARMONIC'

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.inputs.new('SvStringsSocket', "Polygons")
            self.inputs.new('SvStringsSocket', "ScalarValue")
            self.inputs.new('SvVerticesSocket', "VectorValue")
            # for checking purpose
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Polygons")
            self.outputs.new('SvVerticesSocket', "Grad")
            self.outputs.new('SvStringsSocket', "Div")
            self.outputs.new('SvStringsSocket', "Curl")
            self.update_sockets(context)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'operation', text='')

        @throttle_and_update_node
        def update_sockets(self, context):

            if self.operation == 'GRAD':
                self.inputs['ScalarValue'].hide_safe = False
                self.inputs['VectorValue'].hide_safe = True
                self.outputs['Grad'].hide_safe = False
                self.outputs['Div'].hide_safe = True
                self.outputs['Curl'].hide_safe = True

            else:
                self.inputs['ScalarValue'].hide_safe = True
                self.inputs['VectorValue'].hide_safe = False
                self.outputs['Grad'].hide_safe = True
                self.outputs['Div'].hide_safe = False
                self.outputs['Curl'].hide_safe = False

        operation: EnumProperty(
            name="Operation",
            items=operation_modes,
            default='GRAD',
            update=update_sockets)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            verts = self.inputs['Vertices'].sv_get(default=[[None]])
            faces = self.inputs['Polygons'].sv_get(default=[[None]])

            # outputs
            if self.outputs['Vertices'].is_linked:
                self.outputs['Vertices'].sv_set(verts)

            if self.outputs['Polygons'].is_linked:
                self.outputs['Polygons'].sv_set(faces)


def register():
    bpy.utils.register_class(SvDifferentialGeometryNode)


def unregister():
    bpy.utils.unregister_class(SvDifferentialGeometryNode)
