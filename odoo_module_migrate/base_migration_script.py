import os
from .config import _ALLOWED_EXTENSIONS
from .tools import _execute_shell
from .log import logger
from . import tools
import re
import pathlib


class BaseMigrationScript(object):
    _TEXT_REPLACES = {}
    _TEXT_ERRORS = {}
    _DEPRECATED_MODULES = []
    _FILE_RENAMES = {}
    _GLOBAL_FUNCTIONS = {}
    _module_path = ''

    def __init__(self):
        pass

    def run(self,
            module_path,
            manifest_path,
            module_name,
            migration_steps,
            directory_path,
            commit_enabled):
        logger.debug('Running %s script' % self.name)
        file_renames = self._FILE_RENAMES or {}
        text_replaces = self._TEXT_REPLACES or {}
        text_errors = self._TEXT_ERRORS or {}
        global_functions = self._GLOBAL_FUNCTIONS or {}
        deprecated_modules = self._DEPRECATED_MODULES or {}

        current_manifest_file_name = manifest_path.as_posix().split('/')[-1]
        if current_manifest_file_name in file_renames:
            new_manifest_file_name = manifest_path.as_posix().replace(
                current_manifest_file_name,
                file_renames[current_manifest_file_name]
            )
            manifest_path = pathlib.Path(new_manifest_file_name)

        for root, directories, filenames in os.walk(module_path.resolve()):
            for filename in filenames:
                # Skip useless file
                # TODO, skip files present in some folders. (for exemple 'lib')
                extension = os.path.splitext(filename)[1]
                if extension not in _ALLOWED_EXTENSIONS:
                    continue

                absolute_file_path = os.path.join(root, filename)
                logger.debug("Migrate '%s' file" % absolute_file_path)

                # Rename file, if required
                new_name = file_renames.get(filename)
                if new_name:
                    self._rename_file(
                        directory_path,
                        absolute_file_path,
                        os.path.join(root, new_name),
                        commit_enabled
                    )
                    absolute_file_path = os.path.join(root, new_name)

                # Operate changes in the file (replacements, removals)
                replaces = text_replaces.get("*", {})
                replaces.update(text_replaces.get(extension, {}))

                new_text = tools._replace_in_file(
                    absolute_file_path, replaces,
                    "Change file content of %s" % filename)

                # Display errors if the new content contains some obsolete
                # pattern
                errors = text_errors.get("*", {})
                errors.update(text_errors.get(extension, {}))
                for pattern, error_message in errors.items():
                    if re.findall(pattern, new_text):
                        logger.error(error_message)

        # Handle deprecated modules
        current_manifest_text = tools._read_content(manifest_path)
        new_manifest_text = current_manifest_text
        for items in deprecated_modules:
            old_module, action = items[0:2]
            new_module = len(items) > 2 and items[2]
            old_module_pattern = r"('|\"){0}('|\")".format(old_module)
            if new_module:
                new_module_pattern = r"('|\"){0}('|\")".format(new_module)
                replace_pattern = r"\1{0}\2".format(new_module)

            if not re.findall(old_module_pattern, new_manifest_text):
                continue

            if action == 'removed':
                # The module has been removed, just log an error.
                logger.error(
                    "Depends on removed module '%s'" % (old_module))

            elif action == 'renamed':
                new_manifest_text = re.sub(
                    old_module_pattern, replace_pattern, new_manifest_text)
                logger.info(
                    "Replaced dependency of '%s' by '%s'." % (
                        old_module, new_module))

            elif action == 'oca_moved':
                new_manifest_text = re.sub(
                    old_module_pattern, replace_pattern, new_manifest_text)
                logger.warning(
                    "Replaced dependency of '%s' by '%s' (%s)\n"
                    "Check that '%s' is available on your system." % (
                        old_module, new_module, items[3], new_module))

            elif action == "merged":
                if not re.findall(new_module_pattern, new_manifest_text):
                    # adding dependency of the merged module
                    new_manifest_text = re.sub(
                        old_module_pattern, replace_pattern, new_manifest_text)
                    logger.info(
                        "'%s' merged in '%s'. Replacing dependency." % (
                            old_module, new_module))
                else:
                    # TODO, improve me. we should remove the dependency
                    # but it could generate coma trouble.
                    # maybe handling this treatment by ast lib could fix
                    # the problem.
                    logger.error(
                        "'%s' merged in '%s'. You should remove the"
                        " dependency to '%s' manually." % (
                            old_module, new_module, old_module))

        if current_manifest_text != new_manifest_text:
            tools._write_content(manifest_path, new_manifest_text)

        if global_functions:
            for function in global_functions:
                function(
                    logger=logger,
                    module_path=module_path,
                    module_name=module_name,
                    manifest_path=manifest_path,
                    migration_steps=migration_steps,
                    tools=tools,
                )

    def _rename_file(self,
                     module_path,
                     old_file_path,
                     new_file_path,
                     commit_enabled):
        """
        Rename a file. try to execute 'git mv', to avoid huge diff.

        if 'git mv' fails, make a classical rename
        """
        logger.info(
            "Renaming file: '%s' by '%s' " % (
                old_file_path.replace(str(module_path.resolve()), ""),
                new_file_path.replace(str(module_path.resolve()), ""))
        )
        if commit_enabled:
            _execute_shell(
                "git mv %s %s" % (old_file_path, new_file_path),
                path=module_path)
        else:
            _execute_shell(
                "mv %s %s" % (old_file_path, new_file_path),
                path=module_path
            )