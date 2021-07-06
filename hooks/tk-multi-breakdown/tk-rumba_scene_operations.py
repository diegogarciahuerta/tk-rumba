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


from tank import Hook
import os


__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


import rumba

import sgtk.util


def find_nodes_with_reference(node, results=None):
    """
    Recursively find nodes that have been referenced within the hierarchy of
    a given a root node.
    """
    if results is None:
        results = []

    if node.reference_filename():
        results.append(node)

    for child_node in node.children():
        find_nodes_with_reference(child_node, results=results)

    return results


def find_nodes_with_plug(node, plug_name, type_names=None, results=None):
    """
    Recursively finds nodes with plugs with a specified name within the
    hierarchy of a given a root node. Optionally we can specify a list of node
    types to filter by.
    """

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


def get_node_file_path(node):
    """
    Retrieve the file path referenced by nodes of different types.
    Suppoted types are: Asset, UsdAsset, and Media nodes
    """
    if node.type_name() in ["Asset"]:
        return node.reference_filename()
    elif node.type_name() in ["UsdAsset"]:
        return node.plug("file_path").as_string()
    elif node.type_name() in ["Media"]:
        return node.plug("file").as_string()


def set_node_file_path(node, path):
    """
    Set the file path referenced by nodes of different types.
    Suppoted types are: Asset, UsdAsset, and Media nodes
    """
    if node.type_name() in ["Asset"]:
        return node.replace_reference(path)
    elif node.type_name() in ["UsdAsset"]:
        return node.plug("file_path").set_value(path)
    elif node.type_name() in ["Media"]:
        return node.plug("file").set_value(path)


# let's put some color to these gray-ish UIs
ITEM_COLORS = {
    "Asset": "#e7a81d",
    "UsdAsset": "#a8e71d",
    "Media": "#1da8e7",
    "default": "#a81de7",
}


class BreakdownSceneItem(str):
    """
    Helper Class to store metadata per update item.

    tk-multi-breakdown requires item['node'] to be a str. This is what is displayed in
    the list of recognized items to update. We want to add metadata to each item
    as what we want to display as name is not the actual item to update.
    As a str is required we are forced to inherit from str instead of the more
    python friendly object + __repr__ magic method.
    """

    def __new__(cls, node, file_path):
        node_name = node.full_document_name()
        node_type = node.type_name()
        node_color = ITEM_COLORS.get(node_type, ITEM_COLORS["default"])
        text = (
            "<span style='color:%s'><b>%s</b></span>"
            "<br/><nobr><b><sub>%s</sub></b></nobr>"
            % (node_color, node_name, node_type)
        )

        item = str.__new__(cls, text)
        item.node = node_name
        item.node_type = node_type

        return item


class BreakdownSceneOperations(Hook):
    """
    Breakdown operations for Rumba.

    This implementation handles detection of rumba read and write nodes.
    """

    def scan_scene(self):
        """
        The scan scene method is executed once at startup and its purpose is
        to analyze the current scene and return a list of references that are
        to be potentially operated on.

        The return data structure is a list of dictionaries. Each scene
        reference that is returned should be represented by a dictionary with
        three keys:

        - "attr": The filename attribute of the 'node' that is to be operated
           on. Most DCCs have a concept of a node, attribute, path or some
           other way to address a particular object in the scene.
        - "type": The object type that this is. This is later passed to the
           update method so that it knows how to handle the object.
        - "path": Path on disk to the referenced object.

        Toolkit will scan the list of items, see if any of the objects matches
        any templates and try to determine if there is a more recent version
        available. Any such versions are then displayed in the UI as out of
        date.
        """
        # this is a bit dogy, but works, we hide the update
        # button as it is not needed.
        refs = []

        active_document = rumba.active_document()
        if active_document:
            nodes = find_nodes_with_reference(active_document) or []
            nodes += find_nodes_with_plug(
                active_document, "file_path", type_names=["UsdAsset"]
            )
            nodes += find_nodes_with_plug(active_document, "file", type_names=["Media"])

            for node in nodes:
                ref_path = get_node_file_path(node)
                if ref_path:
                    refs.append(
                        {
                            "node": BreakdownSceneItem(node, ref_path),
                            "type": "file",
                            "path": ref_path,
                        }
                    )

        app = self.parent
        engine = app.engine
        engine.log_debug("refs: %s" % refs)

        return refs

    def update(self, items):
        """
        Perform replacements given a number of scene items passed from the app.

        Once a selection has been performed in the main UI and the user clicks
        the update button, this method is called.

        The items parameter is a list of dictionaries on the same form as was
        generated by the scan_scene hook above. The path key now holds
        the that each attribute should be updated *to* rather than the current
        path.
        """
        app = self.parent
        engine = app.engine
        engine.log_debug("items: %s" % items)

        active_document = rumba.active_document()
        if active_document:
            rumba.modify_begin("Shotgun Update References")
            for i in items:
                new_path = i["path"]
                node_name = i["node"].node
                node = active_document.child(node_name)
                engine.log_debug("Updating node: %s to path %s" % (node_name, new_path))
                set_node_file_path(node, new_path)
            rumba.modify_end()
