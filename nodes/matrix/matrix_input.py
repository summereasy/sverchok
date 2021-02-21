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

from math import *
import numpy as np
from mathutils import Matrix

import bpy
from bpy.props import StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, zip_long_repeat, throttle_and_update_node
from sverchok.utils import logging
from sverchok.utils.modules.eval_formula import get_variables, safe_eval


class SvMatrixInput(bpy.types.Node, SverchCustomTreeNode):
    ''' MatrixInput '''
    bl_idname = 'SvMatrixInput'
    bl_label = 'Matrix Formula'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_INPUT'

    @throttle_and_update_node
    def on_update(self, context):
        self.adjust_sockets()

    formula1: StringProperty(default="1", update=on_update)
    formula2: StringProperty(default="0", update=on_update)
    formula3: StringProperty(default="0", update=on_update)
    formula4: StringProperty(default="0", update=on_update)
    formula5: StringProperty(default="1", update=on_update)
    formula6: StringProperty(default="0", update=on_update)
    formula7: StringProperty(default="0", update=on_update)
    formula8: StringProperty(default="0", update=on_update)
    formula9: StringProperty(default="1", update=on_update)

    def formulas(self):
        return [self.formula1, self.formula4, self.formula7,
                self.formula2, self.formula5, self.formula8,
                self.formula3, self.formula6, self.formula9]

    def formula(self, k):
        return self.formulas()[k]

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        for i in range(3):
            row = col.row(align=True)
            for j in range(i, 9, 3):
                if j == 0:
                    row.prop(self, "formula1", text="", index=j)
                if j == 1:
                    row.prop(self, "formula2", text="", index=j)
                if j == 2:
                    row.prop(self, "formula3", text="", index=j)
                if j == 3:
                    row.prop(self, "formula4", text="", index=j)
                if j == 4:
                    row.prop(self, "formula5", text="", index=j)
                if j == 5:
                    row.prop(self, "formula6", text="", index=j)
                if j == 6:
                    row.prop(self, "formula7", text="", index=j)
                if j == 7:
                    row.prop(self, "formula8", text="", index=j)
                if j == 8:
                    row.prop(self, "formula9", text="", index=j)

    def sv_init(self, context):
        self.outputs.new('SvMatrixSocket', "Matrix")
        self.width = 300

    def get_variables(self):
        variables = set()

        for formula in self.formulas():
            vs = get_variables(formula)
            variables.update(vs)

        return list(sorted(list(variables)))

    def adjust_sockets(self):
        variables = self.get_variables()
        #self.debug("adjust_sockets:" + str(variables))
        #self.debug("inputs:" + str(self.inputs.keys()))
        for key in self.inputs.keys():
            if (key not in variables) and (key in self.inputs):
                self.debug("Input {} not in variables {}, remove it".format(
                    key, str(variables)))
                self.inputs.remove(self.inputs[key])
        for v in variables:
            if v not in self.inputs:
                self.debug("Variable {} not in inputs {}, add it".format(
                    v, str(self.inputs.keys())))
                self.inputs.new('SvStringsSocket', v)

    def sv_update(self):
        '''
        update analyzes the state of the node and returns if the criteria to start processing
        are not met.
        '''

        if not any(len(formula) for formula in self.formulas()):
            return

        self.adjust_sockets()

    def get_input(self):
        variables = self.get_variables()
        inputs = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                inputs[var] = self.inputs[var].sv_get()

        return inputs

    def process(self):

        if not self.outputs['Matrix'].is_linked:
            return

        var_names = self.get_variables()
        inputs = self.get_input()

        results = []

        if var_names:
            input_values = [inputs.get(name, [[0]]) for name in var_names]
            parameters = match_long_repeat(input_values)
        else:
            parameters = [[[None]]]
        for objects in zip(*parameters):
            for values in zip_long_repeat(*objects):
                variables = dict(zip(var_names, values))
                vector = []
                for formula in self.formulas():
                    if formula:
                        value = safe_eval(formula, variables)
                        vector.append(value)
                        # print(f"vector = {vector}")
                matrix = np.array(vector).reshape(3, 3)
                # print(f"matrix = {matrix}")
                results.append(Matrix(matrix).to_4x4())
                # print(f"results = {results}")

        self.outputs[0].sv_set(results)


def register():
    bpy.utils.register_class(SvMatrixInput)


def unregister():
    bpy.utils.unregister_class(SvMatrixInput)
