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
This file is loaded automatically by the DCC app at startup
It sets up the Toolkit context and prepares the engine.
"""

import os
import sys
import traceback

import logging
import logging.handlers

import rumba

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


ENGINE_NAME = "tk-rumba"


SGTK_MODULE_PATH = os.environ.get("SGTK_MODULE_PATH")
if SGTK_MODULE_PATH and SGTK_MODULE_PATH not in sys.path:
    sys.path.insert(0, SGTK_MODULE_PATH)

try:
    import sgtk
except ImportError as e:
    msg = "Shotgun: Could not import sgtk!: %s" % e
    raise ImportError(msg)


logger = sgtk.LogManager.get_logger(__name__)


def display_error(msg):
    print(("Shotgun Error | %s | %s " % (ENGINE_NAME, msg)))


def display_warning(msg):
    print(("Shotgun Warning | %s | %s " % (ENGINE_NAME, msg)))


def display_info(msg):
    print(("Shotgun Info | %s | %s " % (ENGINE_NAME, msg)))


def start_toolkit_classic(logger):
    """
    Parse enviornment variables for an engine name and
    serialized Context to use to startup Toolkit,
    the engine and environment.
    """

    logger.debug("Launching toolkit in classic mode.")

    # Get the name of the engine to start from the environement
    env_engine = os.environ.get("SGTK_ENGINE")
    if not env_engine:
        msg = "Shotgun: Missing required environment variable SGTK_ENGINE."
        display_error(msg)
        return

    # Get the context load from the environment.
    env_context = os.environ.get("SGTK_CONTEXT")
    if not env_context:
        msg = "Shotgun: Missing required environment variable SGTK_CONTEXT."
        display_error(msg)
        return
    try:
        # Deserialize the environment context
        context = sgtk.context.deserialize(env_context)
    except Exception as e:
        msg = (
            "Shotgun: Could not create context! Shotgun Pipeline Toolkit"
            " will be disabled. Details: %s" % e
        )
        etype, value, tb = sys.exc_info()
        msg += "".join(traceback.format_exception(etype, value, tb))
        display_error(msg)
        return

    try:
        # Start up the toolkit engine from the environment data
        logger.debug(
            "Launching engine instance '%s' for context %s" % (env_engine, env_context)
        )
        sgtk.platform.start_engine(env_engine, context.sgtk, context)
    except Exception as e:
        msg = "Shotgun: Could not start engine. Details: %s" % e
        etype, value, tb = sys.exc_info()
        msg += "".join(traceback.format_exception(etype, value, tb))
        display_error(msg)
        return


def start_toolkit():
    """
    Import Toolkit and start up the engine based on
    environment variables.
    """

    # Verify sgtk can be loaded.
    try:
        import sgtk
    except Exception as e:
        msg = "Shotgun: Could not import sgtk! Disabling for now: %s" % e
        display_error(msg)
        return

    # start up toolkit logging to file
    sgtk.LogManager().initialize_base_file_handler(ENGINE_NAME)

    logger = sgtk.LogManager.get_logger(__name__)

    # Rely on the classic boostrapping method
    start_toolkit_classic(logger)

    # Check if a file was specified to open and open it.
    file_to_open = os.environ.get("SGTK_FILE_TO_OPEN")
    if file_to_open:
        msg = "Shotgun: Opening '%s'..." % file_to_open
        display_info(msg)
        rumba.load_document(file_to_open)

    # Clean up temp env variables.
    del_vars = ["SGTK_ENGINE", "SGTK_CONTEXT", "SGTK_FILE_TO_OPEN"]
    for var in del_vars:
        if var in os.environ:
            del os.environ[var]


start_toolkit()
