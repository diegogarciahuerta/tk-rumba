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

import sgtk
from sgtk.util.filesystem import ensure_folder_exists

import fbx
import rumba

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


HookBaseClass = sgtk.get_hook_baseclass()


class RumbaNodePublishPlugin(HookBaseClass):
    """
    Plugin for publishing an rumba controllers animation to an FBX file.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    """

    @property
    def type_description(self):
        return "Rumba Node"

    @property
    def short_description(self):
        return "Rumba Node"

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["rumba.*", "file.rumba"]
        """
        return ["rumba.node"]

    def _export(self, settings, item, path):
        node_full_document_name = item.properties.get("node_full_document_name")
        active_document = rumba.active_document()
        if active_document:
            node = active_document.child(node_full_document_name)
            if node:
                folder = os.path.dirname(path)
                ensure_folder_exists(folder)
                node.write(path)
