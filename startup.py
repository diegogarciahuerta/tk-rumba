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
import sys
import cgitb


import sgtk
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation
from sgtk.pipelineconfig_utils import get_sgtk_module_path


__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


ENGINE_NAME = "tk-rumba"
APPLICATION_NAME = "Rumba"

logger = sgtk.LogManager.get_logger(__name__)

# Let's enable cool and detailed tracebacks
cgitb.enable(format="text")


class RumbaLauncher(SoftwareLauncher):
    """
    Handles launching application executables. Automatically starts up
    the shotgun engine with the current context in the new session
    of the application.
    """

    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and products. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place
    COMPONENT_REGEX_LOOKUP = {
        "platform": r"\(x86\)|\(x64\)",
        "platform_version": r"\(x86\)|\(x64\)",
    }

    # This dictionary defines a list of executable template strings for each
    # of the supported operating systems. The templates are used for both
    # globbing and regex matches by replacing the named format placeholders
    # with an appropriate glob or regex string.

    EXECUTABLE_TEMPLATES = {
        "darwin": ["$RUMBA_BIN", "/Applications/rumba/Rumba/Rumba.app"],
        "win32": [
            "$RUMBA_BIN",
            "C:/Program Files/Rumba/rumba.exe",
        ],
        "linux": ["$RUMBA_BIN", "/usr/bin/rumba"],
    }

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch in that will automatically
        load Toolkit and the engine when the application starts.

        :param str exec_path: Path to application executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on
                                            launch.
        :returns: :class:`LaunchInformation` instance
        """
        required_env = {}

        # Run the engine's init.py file when the application starts up
        resources_plugins_path = os.path.join(self.disk_location, "startup")
        required_env["RUMBA_USER_PLUGINS"] = (
            os.environ.get("RUMBA_USER_PLUGINS", "")
            + os.pathsep
            + resources_plugins_path
        )

        # Prepare the launch environment with variables required by the
        # classic bootstrap approach.
        self.logger.debug(
            "Preparing %s Launch via Toolkit Classic methodology ..." % APPLICATION_NAME
        )

        required_env["SGTK_ENGINE"] = ENGINE_NAME
        required_env["SGTK_CONTEXT"] = sgtk.context.serialize(self.context)
        required_env["SGTK_MODULE_PATH"] = get_sgtk_module_path()

        if file_to_open:
            # Add the file name to open to the launch environment
            required_env["SGTK_FILE_TO_OPEN"] = file_to_open

        return LaunchInformation(path=exec_path, args=args, environ=required_env)

    def _icon_from_engine(self):
        """
        Use the default engine icon as the application does not supply
        an icon in their software directory structure.

        :returns: Full path to application icon as a string or None.
        """

        # the engine icon
        engine_icon = os.path.join(self.disk_location, "icon_256.png")
        return engine_icon

    def scan_software(self):
        """
        Scan the filesystem for the application executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """
        self.logger.debug("Scanning for %s executables..." % APPLICATION_NAME)

        supported_sw_versions = []
        for sw_version in self._find_software():
            supported_sw_versions.append(sw_version)

        return supported_sw_versions

    def _find_software(self):
        """
        Find executables in the default install locations.
        """

        # all the executable templates for the current OS
        executable_templates = self.EXECUTABLE_TEMPLATES.get(
            "darwin"
            if sgtk.util.is_macos()
            else "win32"
            if sgtk.util.is_windows()
            else "linux"
            if sgtk.util.is_linux()
            else []
        )

        # all the discovered executables
        sw_versions = []

        # Here we account for extra arguments passed to the blender command line
        # this allows a bit of flexibility without having to fork the whole
        # engine just for this reason.
        # Unfortunately this cannot be put in the engine.yml as I would like
        # to because the engine class has not even been instantiated yet.
        extra_args = os.environ.get("SGTK_RUMBA_CMD_EXTRA_ARGS")

        for executable_template in executable_templates:
            executable_template = os.path.expanduser(executable_template)
            executable_template = os.path.expandvars(executable_template)

            self.logger.debug("Processing template %s.", executable_template)

            executable_matches = self._glob_and_match(
                executable_template, self.COMPONENT_REGEX_LOOKUP
            )

            # Extract all products from that executable.
            for (executable_path, key_dict) in executable_matches:
                # no way to extract the version from this application, so no
                # version is available to display
                executable_version = " "

                args = []
                if extra_args:
                    args.append(extra_args)

                sw_versions.append(
                    SoftwareVersion(
                        executable_version,
                        APPLICATION_NAME,
                        executable_path,
                        icon=self._icon_from_engine(),
                        args=args,
                    )
                )

        return sw_versions
