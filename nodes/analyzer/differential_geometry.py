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
import sys
from bpy.props import EnumProperty, FloatProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, throttle_and_update_node
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import scipy

operations = [
    ('GRAD', 'Gradient'),
    ('DIV_CURL', 'Div and Curl')
    # ('LAPLACE', 'Laplacian Matrix', [('Vertices', 'Polygons')], [('Laplacian Matrix')]),
    # ('MASS', 'Mass Matrix', [('Vertices', 'Polygons')], [('Mass Matrix')])
]

scalar_ops = {'GRAD'}

operation_modes = [(id, name, name, i)
                   for i, (id, name) in enumerate(operations)]

sys.path.append('/opt/anaconda3/envs/trimesh/lib/python3.7/site-packages/')
import trimesh

sys.path.append('/Users/zhaowei/Documents/Study/DDG/libs')
from mesh_calculus import gradient, divergence, curl


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
            self.inputs.new('SvStringsSocket', "Scale").prop_name = 'scale'
            self.outputs.new('SvVerticesSocket', "Position")
            self.outputs.new('SvVerticesSocket', "Gradient")
            self.outputs.new('SvStringsSocket', "Divergence")
            self.outputs.new('SvStringsSocket', "Curl")
            # self.outputs.new('SvVerticesSocket', "Vertices")
            # self.outputs.new('SvStringsSocket', "Polygons")
            self.update_sockets(context)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'operation', text='')

        @throttle_and_update_node
        def update_sockets(self, context):

            if self.operation == 'GRAD':
                self.inputs['ScalarValue'].hide_safe = False
                self.inputs['VectorValue'].hide_safe = True
                self.outputs['Gradient'].hide_safe = False
                self.outputs['Position'].hide_safe = False
                self.outputs['Divergence'].hide_safe = True
                self.outputs['Curl'].hide_safe = True

            else:
                self.inputs['ScalarValue'].hide_safe = True
                self.inputs['VectorValue'].hide_safe = False
                self.outputs['Gradient'].hide_safe = True
                self.outputs['Position'].hide_safe = True
                self.outputs['Divergence'].hide_safe = False
                self.outputs['Curl'].hide_safe = False

            updateNode(self, context)

        scale: FloatProperty(
            name='Size', description='Size of Gradient', default=10.0, update=updateNode)
        # TODO: BoolProperty to add Normalized OUTPUT for Gradient

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
            sVals = self.inputs['ScalarValue'].sv_get(default=[[None]])
            vVals = self.inputs['VectorValue'].sv_get(default=[[None]])
            scale = self.inputs['Scale'].sv_get(default=[[None]])

            Position = []
            Gradient = []
            Div = []
            Curl = []
            if self.operation == 'GRAD':
                for v, p, sVal in zip(verts, faces, sVals):
                    mesh = trimesh.Trimesh(v, p, process=False)
                    S = np.array(sVal)
                    G = gradient(S, mesh, rotated=False).T
                    Gr = gradient(S, mesh, rotated=True).T
                    tri_centers = mesh.vertices[mesh.faces].mean(axis=1)
                    Gradient.append((G * scale).tolist())
                    Position.append(tri_centers.tolist())

            elif self.operation == 'DIV_CURL':
                for v, p, vVal in zip(verts, faces, vVals):
                    mesh = trimesh.Trimesh(v, p, process=False)
                    V = np.array(vVal)
                    # V_centers = V[mesh.faces].mean(axis=1) #Don't know why not very Accurate
                    D = divergence(V, mesh)
                    C = curl(V, mesh)
                    Div.append(D.tolist())
                    Curl.append(C.tolist())

            # outputs
            if self.outputs['Position'].is_linked:
                self.outputs['Position'].sv_set(Position)

            if self.outputs['Gradient'].is_linked:
                self.outputs['Gradient'].sv_set(Gradient)

            if self.outputs['Divergence'].is_linked:
                self.outputs['Divergence'].sv_set(Div)

            if self.outputs['Curl'].is_linked:
                self.outputs['Curl'].sv_set(Curl)


def register():
    bpy.utils.register_class(SvDifferentialGeometryNode)


def unregister():
    bpy.utils.unregister_class(SvDifferentialGeometryNode)
