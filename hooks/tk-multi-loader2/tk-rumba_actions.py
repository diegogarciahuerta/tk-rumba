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


"""
Hook that loads defines all the available actions, broken down by publish type.
"""

import os
import sgtk

import rumba
import rumbapy
import rumba_media

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


HookBaseClass = sgtk.get_hook_baseclass()


RUMBA_SUPPORTED_FORMATS = (".rumbanode", ".abc", ".usd", ".usda", ".usdc")
RUMBA_SUPPORTED_MEDIA_FORMATS = (
    rumba_media.audio_formats()[1]
    + rumba_media.image_formats()[1]
    + rumba_media.video_formats()[1]
)


class RumbaActions(HookBaseClass):
    # public interface - to be overridden by deriving classes

    def generate_actions(self, sg_publish_data, actions, ui_area):
        """
        Returns a list of action instances for a particular publish.
        This method is called each time a user clicks a publish somewhere in
        the UI.
        The data returned from this hook will be used to populate the actions
        menu for a publish.

        The mapping between Publish types and actions are kept in a different
        place (in the configuration) so at the point when this hook is called,
        the loader app has already established *which* actions are appropriate
        for this object.

        The hook should return at least one action for each item passed in via
        the actions parameter.

        This method needs to return detailed data for those actions, in the
        form of a list of dictionaries, each with name, params, caption and
        description keys.

        Because you are operating on a particular publish, you may tailor the
        output  (caption, tooltip etc) to contain custom information suitable
        for this publish.

        The ui_area parameter is a string and indicates where the publish is to
        be shown.
        - If it will be shown in the main browsing area, "main" is passed.
        - If it will be shown in the details area, "details" is passed.
        - If it will be shown in the history area, "history" is passed.

        Please note that it is perfectly possible to create more than one
        action "instance" for an action! You can for example do scene
        introspection - if the action passed in is "character_attachment"
        you may for example scan the scene, figure out all the nodes
        where this object can be attached and return a list of action
        instances:
        "attach to left hand", "attach to right hand" etc. In this case,
        when more than one object is returned for an action, use the params
        key to pass additional data into the run_action hook.

        :param sg_publish_data: Shotgun data dictionary with all the standard
                                publish fields.
        :param actions: List of action strings which have been defined in the
                        app configuration.
        :param ui_area: String denoting the UI Area (see above).
        :returns List of dictionaries, each with keys name, params, caption and
         description
        """
        app = self.parent
        app.log_debug(
            "Generate actions called for UI element %s. "
            "Actions: %s. Publish Data: %s" % (ui_area, actions, sg_publish_data)
        )

        action_instances = []

        if "reference" in actions:
            action_instances.append(
                {
                    "name": "reference",
                    "params": None,
                    "caption": "Reference into the current Document",
                    "description": (
                        "This file will be referenced into the current Document"
                    ),
                }
            )

        if "import" in actions:
            action_instances.append(
                {
                    "name": "import",
                    "params": None,
                    "caption": "Import into the current Document",
                    "description": (
                        "This file will be imported into the current Document"
                    ),
                }
            )

        if "import_media" in actions:
            action_instances.append(
                {
                    "name": "import_media",
                    "params": None,
                    "caption": "Import media into the current Session",
                    "description": (
                        "This file will be imported as a media into the current session"
                    ),
                }
            )

        return action_instances

    def execute_multiple_actions(self, actions):
        """
        Executes the specified action on a list of items.

        The default implementation dispatches each item from ``actions`` to
        the ``execute_action`` method.

        The ``actions`` is a list of dictionaries holding all the actions to
        execute.
        Each entry will have the following values:

            name: Name of the action to execute
            sg_publish_data: Publish information coming from Shotgun
            params: Parameters passed down from the generate_actions hook.

        .. note::
            This is the default entry point for the hook. It reuses the
            ``execute_action`` method for backward compatibility with hooks
            written for the previous version of the loader.

        .. note::
            The hook will stop applying the actions on the selection if an
            error is raised midway through.

        :param list actions: Action dictionaries.
        """
        app = self.parent
        for single_action in actions:
            app.log_debug("Single Action: %s" % single_action)
            name = single_action["name"]
            sg_publish_data = single_action["sg_publish_data"]
            params = single_action["params"]

            self.execute_action(name, params, sg_publish_data)

    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.

        :param name: Action name string representing one of the items returned
                     by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Shotgun data dictionary with all the standard
                                publish fields.
        :returns: No return value expected.
        """
        app = self.parent
        app.log_debug(
            "Execute action called for action `%s`. "
            "Parameters: %s. Publish Data: %s" % (name, params, sg_publish_data)
        )

        # resolve path
        # toolkit uses utf-8 encoded strings internally and Rumba API expects
        # unicode so convert the path to ensure filenames containing complex
        # characters are supported
        path = self.get_publish_path(sg_publish_data).replace(os.path.sep, "/")
        app.log_debug("Publish path: %s" % path)

        if name == "reference":
            if not self._is_a_supported_extension(path, sg_publish_data):
                raise Exception("Unsupported file extension for '%s'!" % path)
            self._reference_into_current_document(path, sg_publish_data)
        elif name == "import":
            if not self._is_a_supported_extension(path, sg_publish_data):
                raise Exception("Unsupported file extension for '%s'!" % path)
            self._import_into_current_document(path, sg_publish_data)
        elif name == "import_media":
            if not self._is_a_supported_media_extension(path, sg_publish_data):
                raise Exception("Unsupported file extension for '%s'!" % path)
            self._import_media_into_new_media_layer(path, sg_publish_data)

    def _is_a_supported_extension(self, path, sg_publish_data):
        _, ext = os.path.splitext(path)
        return ext.lower() in RUMBA_SUPPORTED_FORMATS

    def _is_a_supported_media_extension(self, path, sg_publish_data):
        _, ext = os.path.splitext(path)
        return ext.lower() in RUMBA_SUPPORTED_MEDIA_FORMATS

    def _reference_into_current_document(self, path, sg_publish_data):
        """
        References a file into the current document

        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard
                                publish fields.
        """
        app = self.parent
        active_document = rumba.active_document()

        if active_document:
            if os.path.exists(path):
                app.log_debug("Referencing path: %s" % path)
                rumba.modify_begin("Shotgun Reference File")
                rumba.reference(active_document, path, "")
                rumba.modify_end()
            else:
                app.log_warning("Referencing path not found!: %s" % path)

    def _import_into_current_document(self, path, sg_publish_data):
        """
        Imports a file into the current document

        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard
                                publish fields.
        """
        app = self.parent
        active_document = rumba.active_document()

        if active_document:
            if os.path.exists(path):
                app.log_debug("Importing path: %s" % path)
                rumba.modify_begin("Shotgun Import File")
                rumba.load_node(active_document, path, "")
                rumba.modify_end()
            else:
                app.log_warning("Path to import not found!: %s" % path)

    def _import_media_into_new_media_layer(self, path, sg_publish_data):
        """
        Imports a file into the current document

        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard
                                publish fields.
        """
        app = self.parent
        active_document = rumba.active_document()

        if active_document:
            if os.path.exists(path):
                rumba.modify_begin("Shotgun Import File")
                layer_name = sg_publish_data.get("code", os.path.basename(path))
                media_layer = rumbapy.add_media_layer(layer_name)
                frame = rumba.current_frame()
                media_node = rumbapy.get_media(path)
                rumbapy.add_media_clip(media_layer, media_node, frame)
                rumba.modify_end()
            else:
                app.log_warning("Path to import not found!: %s" % path)
