# ----------------------------------------------------------------------------
# Copyright (c) 2021, Diego Garcia Huerta.
#
# Your use of this software as distributed in this GitHub repository, is
# governed by the MIT License
#
# Your use of the Shotgun Pipeline Toolkit is governed by the applicable
# license agreement between you and Autodesk / Shotgun.
#
# Read LICENSE and SHOTGUN_LICENSE for full details about the licenses that
# pertain to this software.
# ----------------------------------------------------------------------------


import sgtk
from sgtk import TankError

import rumba

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


HookBaseClass = sgtk.get_hook_baseclass()


class FrameOperation(HookBaseClass):
    """
    Hook called to perform a frame operation with the
    current scene
    """

    def get_frame_range(self, **kwargs):
        """
        get_frame_range will return a tuple of (in_frame, out_frame)
        :returns: Returns the frame range in the form (in_frame, out_frame)
        :rtype: tuple[int, int]
        """

        current_in = 0
        current_out = 0

        active_doc = rumba.active_document()

        if active_doc:
            current_in = active_doc.start_frame.value().as_int()
            current_out = active_doc.end_frame.value().as_int()

        return (current_in, current_out)

    def set_frame_range(self, in_frame=None, out_frame=None, **kwargs):
        """
        set_frame_range will set the frame range using `in_frame` and `out_frame`
        :param int in_frame: in_frame for the current context
            (e.g. the current shot, current asset etc)
        :param int out_frame: out_frame for the current context
            (e.g. the current shot, current asset etc)
        """

        active_doc = rumba.active_document()

        if active_doc:
            start = int(in_frame)
            end = int(out_frame)

            rumba.modify_begin("Shotgun Update Frame Range")
            active_doc.start_frame.set_value(start)
            active_doc.end_frame.set_value(end)
            active_doc.range_start_frame.set_value(start)
            active_doc.range_end_frame.set_value(end)
            rumba.modify_end()
