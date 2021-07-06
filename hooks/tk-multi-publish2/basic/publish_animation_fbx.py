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

import fbx

from rumbapy import widget, message_box, Progress

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


HookBaseClass = sgtk.get_hook_baseclass()


class RumbaFBXPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an rumba controllers animation to an FBX file.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """
        # inherit the settings from the base publish plugin
        base_settings = super(RumbaFBXPublishPlugin, self).settings or {}

        # settings specific to this class
        fbx_export_publish_settings = {
            "Export Namespaces": {
                "type": bool,
                "default": True,
                "description": "if True, add a Maya style namespace to each referenced nodes"
                ", like Maya does with references. The namespace is the name "
                "of the Asset root node.",
            }
        }

        # update the base settings
        base_settings.update(fbx_export_publish_settings)

        return base_settings

    @property
    def type_description(self):
        return "FBX File"

    @property
    def short_description(self):
        return "Animation Controllers as FBX"

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["rumba.*", "file.rumba"]
        """
        return ["rumba.animation.fbx"]

    def _export(self, settings, item, path):
        nodes = []  # export all the assets
        frames = []  # export all the frames
        ascii = False  # we want a binary FBX file
        export_namespaces = True

        # if no nodes are specified, the whole scene is exported
        nodes = item.properties.get("nodes", [])
        extra_fields = item.properties.get("extra_fields", {})
        name = extra_fields.get("name", "scene")

        namespace_setting = settings.get("Export Namespaces")
        if namespace_setting and namespace_setting.value:
            export_namespaces = namespace_setting.value

        try:
            with Progress("Exporting %s as FBX..." % name) as progress:
                fbx.export_nodes(
                    path, nodes, frames, ascii, export_namespaces, progress.update
                )
        except RuntimeError as error:
            message_box(
                "Error exporting to file {}:\n{}".format(path, error),
                title="Exporting Error",
                widget=widget("MainWindow"),
                level="error",
            )
