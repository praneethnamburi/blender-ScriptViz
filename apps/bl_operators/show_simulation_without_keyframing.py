"""
Modal operator example to 'animate' on screen without keyframing.
"""

import bpy

from bpn import new

class ModalTimerOperator(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "wm.modal_timer_operator"
    bl_label = "Modal Timer Operator"

    limits: bpy.props.IntProperty(default=0)
    _timer = None

    def modal(self, context, event):
        print('In Modal')
        if event.type in {'RIGHTMOUSE', 'ESC'} or self.limits > 30:
            self.limits = 0
            self.cancel(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            new.sphere()
            self.limits += 1

        return {'PASS_THROUGH'}

    def execute(self, context):
        print('In execute')
        wm = context.window_manager
        self._timer = wm.event_timer_add(time_step=0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        print('In cancel')
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


def register():
    bpy.utils.register_class(ModalTimerOperator)


def unregister():
    bpy.utils.unregister_class(ModalTimerOperator)

register()

# # test call
# bpy.ops.wm.modal_timer_operator()
