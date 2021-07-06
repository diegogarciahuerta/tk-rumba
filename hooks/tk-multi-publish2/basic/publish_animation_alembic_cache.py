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
import rumba_alembic
from rumbapy import widget, message_box, Progress

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


HookBaseClass = sgtk.get_hook_baseclass()


class RumbaAlembicCachePublishPlugin(HookBaseClass):
    """
    Plugin for publishing animation from Rumba assets as alembic caches.

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
        base_settings = super(RumbaAlembicCachePublishPlugin, self).settings or {}

        # settings specific to this class
        alembic_export_publish_settings = {
            "Sub Samples": {
                "type": list,
                "default": [],
                "description": "A list of sub-samples to export relative to each frame. "
                "If empty, it exports one sample per frame. "
                "Values should be between [-1.0, 1.0]. "
                "For example, samples=[0.0, 0.4] in a frame range from 1 to 3 "
                "would export these  samples : [1.0, 1.4, 2.0, 2.4, 3.0, 3.4].",
            }
        }

        # update the base settings
        base_settings.update(alembic_export_publish_settings)

        return base_settings

    @property
    def type_description(self):
        return "Alembic Cache"

    @property
    def short_description(self):
        return "Animation as Alembic Cache"

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["rumba.*", "file.rumba"]
        """
        return ["rumba.animation.alembic_cache"]

    def _export(self, settings, item, path):

        samples = []  # 1 sample per frame by default

        # let's check the configuration for sub sample preferences
        samples_setting = settings.get("Sub Samples")
        if samples_setting and samples_setting.value:
            samples = samples_setting.value

        # if no nodes are specified, the whole scene is exported
        nodes = item.properties.get("nodes", [])
        extra_fields = item.properties.get("extra_fields", {})
        name = extra_fields.get("name", "scene")

        cyclic = True  # samples if exist would be relative to frame. ie. [0.4, 0.8]
        frame_count = 0

        try:
            with Progress("Exporting %s as Alembic Cache..." % name) as progress:
                rumba_alembic.export_nodes(
                    path,
                    nodes,
                    frame_count=frame_count,
                    samples=samples,
                    cyclic=cyclic,
                    progress=progress.update,
                )
        except RuntimeError as error:
            message_box(
                "Error exporting to file {}:\n{}".format(path, error),
                title="Exporting Error",
                widget=widget("MainWindow"),
                level="error",
            )
