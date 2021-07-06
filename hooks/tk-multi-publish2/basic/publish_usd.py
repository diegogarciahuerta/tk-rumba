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


import os
import traceback
import contextlib

import sgtk
from sgtk import TankError
from tempfile import NamedTemporaryFile
from sgtk.util.version import is_version_older
from sgtk.util.filesystem import copy_file, ensure_folder_exists

import rumba
from rumbapy import widget, action, message_box, Progress
from rumba_Usd import export_to_Usd

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


HookBaseClass = sgtk.get_hook_baseclass()


class RumbaUSDPublishPlugin(HookBaseClass):
    """
    Plugin for publishing a rumba scene/asset as a USD file.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    """

    @property
    def type_description(self):
        return "USD File"

    @property
    def short_description(self):
        return "Animation as USD file"

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["rumba.*", "file.rumba"]
        """
        return ["rumba.animation.usd"]

    def _export(self, settings, item, path):
        nodes = item.properties.get("nodes", [])
        extra_fields = item.properties.get("extra_fields", {})
        name = extra_fields.get("name", "scene")

        try:
            with Progress("Exporting %s to Usd..." % name) as progress:
                export_to_Usd(path, nodes, [], progress.update)
        except RuntimeError as error:
            message_box(
                "Error exporting to file {}:\n{}".format(path, error),
                title="Exporting Error",
                widget=widget("MainWindow"),
                level="error",
            )
