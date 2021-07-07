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
import re
from functools import partial

import sgtk
from sgtk.util.filesystem import create_valid_filename

import rumba

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


HookBaseClass = sgtk.get_hook_baseclass()


def all_ascendants(node, result=None):
    if result is None:
        result = []
    try:
        result.append(node.parent())
        all_ascendants(node.parent(), result=result)
    except RuntimeError:
        pass

    return result


def is_node_visible(node):
    nodes = [node] + all_ascendants(node)
    for node in nodes:
        if node.has_plug("show"):
            if not node.show.as_bool():
                return False
    return True


def find_nodes_with_plug(node, plug_name, type_names=None, results=None):
    if results is None:
        results = []

    if node.has_plug(plug_name):
        # if types were specified filter by them
        if (type_names and node.type_name() in type_names) or type_names is None:
            results.append(node)

    for child_node in node.children():
        find_nodes_with_plug(
            child_node, plug_name, type_names=type_names, results=results
        )

    return results


def find_nodes_of_type(node=None, type_names=None, results=None):
    if node is None:
        node = rumba.active_document()

    if results is None:
        results = []

    # if types were specified filter by them
    if (type_names and node.type_name() in type_names) or type_names is None:
        results.append(node)

    for child_node in node.children():
        find_nodes_of_type(child_node, type_names=type_names, results=results)

    return results


def find_geometry_nodes_by_asset():
    active_document = rumba.active_document()

    nodes = find_nodes_with_plug(active_document, "show", type_names=["Geometry"])
    nodes = [node for node in nodes if is_node_visible(node)]

    by_asset_node = {}
    for node in nodes:
        for p in all_ascendants(node):
            if p.type_name() == "Asset":
                pname = p.asset_name.as_string()
                if pname not in by_asset_node.keys():
                    by_asset_node[pname] = []
                by_asset_node[pname].append(node)
                break

    return by_asset_node


class RumbaSessionCollector(HookBaseClass):
    """
    Collector that operates on the rumba session. Should inherit from the basic
    collector hook.
    """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this collector expects to receive
        through the settings parameter in the process_current_session and
        process_file methods.

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

        # grab any base class settings
        collector_settings = super(RumbaSessionCollector, self).settings or {}

        # settings specific to this collector
        rumba_session_settings = {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for artist work files. Should "
                "correspond to a template defined in "
                "templates.yml. If configured, is made available"
                "to publish plugins via the collected item's "
                "properties. ",
            },
            "Collect Individual Assets": {
                "type": bool,
                "default": True,
                "description": "if True, every asset found in the Rumba scene "
                "will be individually collected for publishing, otherwise the "
                "Rumba scene as a whole is collected for publishing.",
            },
        }

        # update the base settings with these settings
        collector_settings.update(rumba_session_settings)

        return collector_settings

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Rumba and parents a subtree of
        items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        """
        items = []

        # create an item representing the current rumba session
        session_item = self.collect_current_rumba_session(settings, parent_item)
        if session_item:
            items.append(session_item)

            collect_individual_assets = settings.get("Collect Individual Assets").value
            self.parent.logger.debug(
                "Collect Individual Assets: %s" % collect_individual_assets
            )

            if collect_individual_assets:
                usd_asset_items = self.collect_rumba_usd_assets(settings, session_item)
                if usd_asset_items:
                    items.extend(usd_asset_items)
            else:
                usd_scene_item = self.collect_rumba_usd_scene(settings, session_item)
                if usd_scene_item:
                    items.append(usd_scene_item)

            if collect_individual_assets:
                fbx_asset_animation_items = self.collect_rumba_fbx_assets(
                    settings, session_item
                )
                if fbx_asset_animation_items:
                    items.extend(fbx_asset_animation_items)
            else:
                fbx_scene_item = self.collect_rumba_fbx_scene(settings, session_item)
                if fbx_scene_item:
                    items.append(fbx_scene_item)

            if collect_individual_assets:
                abc_asset_items = self.collect_rumba_abc_assets(settings, session_item)
                if abc_asset_items:
                    items.extend(abc_asset_items)
            else:
                abc_animation_item = self.collect_rumba_abc_scene(
                    settings, session_item
                )
                if abc_animation_item:
                    items.append(abc_animation_item)

            rumba_node_item = (
                self.collect_rumba_selection_as_nodes(settings, session_item) or []
            )
            if rumba_node_item:
                items.append(rumba_node_item)

        return items

    def collect_current_rumba_session(self, settings, parent_item):
        """
        Creates an item that represents the current rumba session.

        :param parent_item: Parent Item instance

        :returns: Item of type rumba.session
        """

        publisher = self.parent

        # get the path to the current file
        path = _session_path()

        if not path:
            # no document is active, so nothing to see here!
            return

        # determine the display name for the item
        if path:
            file_info = publisher.util.get_file_path_components(path)
            display_name = file_info["filename"]
        else:
            display_name = "Current Rumba Document"

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            "rumba.session", "Rumba Document", display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "rumba.png")
        session_item.set_icon_from_path(icon_path)

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")

        if work_template_setting:

            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value
            )

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template
            session_item.properties["publish_type"] = "Rumba Document"
            self.logger.debug("Work template defined for Rumba collection.")

        self.logger.info("Collected current Rumba scene")

        return session_item

    def collect_rumba_usd_scene(self, settings, parent_item):
        """
        Creates an item that represents the scene as USD

        :param parent_item: Parent Item instance

        :returns: Item of type rumba.animation.usd
        """

        publisher = self.parent

        # get the path to the current file
        path = _session_path()

        if not path:
            # no document is active, so nothing to see here!
            return

        display_name = "Scene as USD"

        # create the session item for the publish hierarchy
        item = parent_item.create_item("rumba.animation.usd", "USD File", display_name)

        # get the icon path to display for this item
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "usd.png")
        item.set_icon_from_path(icon_path)

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:
            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value
            )

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            item.properties["work_template"] = work_template
            item.properties["publish_type"] = "USD File"

        self.logger.info("Collected Rumba scene as USD for publishing.")

        return item

    def collect_rumba_fbx_scene(self, settings, parent_item):
        """
        Creates an item that represents the controllers animation as FBX

        :param parent_item: Parent Item instance

        :returns: Item of type rumba.animation.fbx
        """

        publisher = self.parent

        # get the path to the current file
        path = _session_path()

        if not path:
            # no document is active, so nothing to see here!
            return

        display_name = "Scene Animation as FBX"

        # create the session item for the publish hierarchy
        item = parent_item.create_item("rumba.animation.fbx", "FBX File", display_name)

        # get the icon path to display for this item
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "fbx.png")
        item.set_icon_from_path(icon_path)

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:
            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value
            )

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            item.properties["work_template"] = work_template
            item.properties["publish_type"] = "FBX File"

        self.logger.info("Collected Rumba animation as FBX for publishing.")

        return item

    def collect_rumba_fbx_assets(self, settings, parent_item):
        """
        Creates an item that represents the publishing of asset animation
        as a USD file.

        :param parent_item: Parent Item instance

        :returns: Item of type rumba.animation.alembic_cache
        """

        publisher = self.parent

        # get the path to the current file
        path = _session_path()

        if not path:
            # no document is active, so nothing to see here!
            return

        by_asset_node = find_geometry_nodes_by_asset()

        items = []
        for asset_name, nodes in by_asset_node.items():

            # let's filter the asset name so we make sure it is
            # alphanumeric, a requirement for the 'name' field
            alphanumeric = re.compile(r"[\W_]+", re.UNICODE)
            asset_name = alphanumeric.sub("", asset_name)

            display_name = "%s FBX Animation" % asset_name

            # create the session item for the publish hierarchy
            item = parent_item.create_item(
                "rumba.animation.fbx", "FBX File", display_name
            )

            # get the icon path to display for this item
            icon_path = os.path.join(self.disk_location, os.pardir, "icons", "fbx.png")
            item.set_icon_from_path(icon_path)

            # if a work template is defined, add it to the item properties so
            # that it can be used by attached publish plugins
            work_template_setting = settings.get("Work Template")
            if work_template_setting:
                work_template = publisher.engine.get_template_by_name(
                    work_template_setting.value
                )

                # store the template on the item for use by publish plugins. we
                # can't evaluate the fields here because there's no guarantee the
                # current session path won't change once the item has been created.
                # the attached publish plugins will need to resolve the fields at
                # execution time.
                item.properties["work_template"] = work_template
                item.properties["publish_type"] = "FBX File"

            item.properties["nodes"] = nodes

            item.properties["extra_fields"] = {"name": asset_name}
            self.logger.info("Asset '%s' collected for FBX publishings" % asset_name)

            items.append(item)

        return items

    def collect_rumba_usd_assets(self, settings, parent_item):
        """
        Creates an item that represents the publishing of asset animation
        as a USD file.

        :param parent_item: Parent Item instance

        :returns: Item of type rumba.animation.alembic_cache
        """

        publisher = self.parent

        # get the path to the current file
        path = _session_path()

        if not path:
            # no document is active, so nothing to see here!
            return

        by_asset_node = find_geometry_nodes_by_asset()

        items = []
        for asset_name, nodes in by_asset_node.items():

            # let's filter the asset name so we make sure it is
            # alphanumeric, a requirement for the 'name' field
            alphanumeric = re.compile(r"[\W_]+", re.UNICODE)
            asset_name = alphanumeric.sub("", asset_name)

            display_name = "%s USD File" % asset_name

            # create the session item for the publish hierarchy
            item = parent_item.create_item(
                "rumba.animation.usd", "USD File", display_name
            )

            # get the icon path to display for this item
            icon_path = os.path.join(self.disk_location, os.pardir, "icons", "usd.png")
            item.set_icon_from_path(icon_path)

            # if a work template is defined, add it to the item properties so
            # that it can be used by attached publish plugins
            work_template_setting = settings.get("Work Template")
            if work_template_setting:
                work_template = publisher.engine.get_template_by_name(
                    work_template_setting.value
                )

                # store the template on the item for use by publish plugins. we
                # can't evaluate the fields here because there's no guarantee the
                # current session path won't change once the item has been created.
                # the attached publish plugins will need to resolve the fields at
                # execution time.
                item.properties["work_template"] = work_template
                item.properties["publish_type"] = "USD File"

            item.properties["nodes"] = nodes

            item.properties["extra_fields"] = {"name": asset_name}
            self.logger.info("Asset '%s' collected for USD publishings" % asset_name)

            items.append(item)

        return items

    def collect_rumba_abc_assets(self, settings, parent_item):
        """
        Creates an item that represents the publishing of asset animation
        as an Alembic Cache file.

        :param parent_item: Parent Item instance

        :returns: Item of type rumba.animation.alembic_cache
        """

        publisher = self.parent

        # get the path to the current file
        path = _session_path()

        if not path:
            # no document is active, so nothing to see here!
            return

        by_asset_node = find_geometry_nodes_by_asset()

        items = []
        for asset_name, nodes in by_asset_node.items():

            # let's filter the asset name so we make sure it is
            # alphanumeric, a requirement for the 'name' field
            alphanumeric = re.compile(r"[\W_]+", re.UNICODE)
            asset_name = alphanumeric.sub("", asset_name)

            display_name = "%s Alembic Cache" % asset_name

            # create the session item for the publish hierarchy
            item = parent_item.create_item(
                "rumba.animation.alembic_cache", "Alembic Cache", display_name
            )

            # get the icon path to display for this item
            icon_path = os.path.join(
                self.disk_location, os.pardir, "icons", "alembic.png"
            )
            item.set_icon_from_path(icon_path)

            # if a work template is defined, add it to the item properties so
            # that it can be used by attached publish plugins
            work_template_setting = settings.get("Work Template")
            if work_template_setting:
                work_template = publisher.engine.get_template_by_name(
                    work_template_setting.value
                )

                # store the template on the item for use by publish plugins. we
                # can't evaluate the fields here because there's no guarantee the
                # current session path won't change once the item has been created.
                # the attached publish plugins will need to resolve the fields at
                # execution time.
                item.properties["work_template"] = work_template
                item.properties["publish_type"] = "Alembic Cache"

            item.properties["nodes"] = nodes

            item.properties["extra_fields"] = {"name": asset_name}
            self.logger.info(
                "Asset '%s' collected for Alembic Cache publishings" % asset_name
            )

            items.append(item)

        return items

    def collect_rumba_abc_scene(self, settings, parent_item):
        """
        Creates an item that represents the publishing of the whole scene
        as an Alembic Cache file.

        :param parent_item: Parent Item instance

        :returns: Item of type rumba.animation.alembic_cache
        """

        publisher = self.parent

        # get the path to the current file
        path = _session_path()

        if not path:
            # no document is active, so nothing to see here!
            return

        display_name = "Scene Alembic Cache"

        # create the session item for the publish hierarchy
        item = parent_item.create_item(
            "rumba.animation.alembic_cache", "Alembic Cache", display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "alembic.png")
        item.set_icon_from_path(icon_path)

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:
            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value
            )

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            item.properties["work_template"] = work_template
            item.properties["publish_type"] = "Alembic Cache"

        self.logger.info("Collected Rumba animation as Alembic Cache for publishing.")

        return item

    def collect_rumba_selection_as_nodes(self, settings, parent_item):
        """
        Creates an item that represents the animation as Alembic Cache to publish.

        :param parent_item: Parent Item instance

        :returns: Item of type rumba.animation.alembic_cache
        """

        publisher = self.parent

        # get the path to the current file
        path = _session_path()

        if not path:
            # no document is active, so nothing to see here!
            return

        selection = rumba.selection()
        if not selection:
            return

        # this is the same behaviour that happens when Save Node is used from
        # the File menu, it multiple nodes are selected, only the first one is
        node = selection[0]
        if node.is_referenced():
            self.logger.warning(
                "Exporting of reference nodes is not supported in Rumba at the moment. The selected node `%s` won't be added for publishing."
                % node.name()
            )
            return None

        node_name = create_valid_filename(node.name())
        display_name = "Node: `%s`" % node.name()

        # create the session item for the publish hierarchy
        item = parent_item.create_item("rumba.node", "Rumba Node", display_name)

        # get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location, os.pardir, "icons", "rumbanode.png"
        )
        item.set_icon_from_path(icon_path)

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:
            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value
            )

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            item.properties["work_template"] = work_template
            item.properties["publish_type"] = "Rumba Node"
            item.properties["node_full_document_name"] = node.full_document_name()
            item.properties["extra_fields"] = {"rumba.node.name": node_name}

        self.logger.info(
            "Collected Selection as Rumba Nodes animation as Alembic Cache for publishing."
        )

        return item


def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = rumba.active_document_filename()
    if path == "untitled":
        path = None

    return path
