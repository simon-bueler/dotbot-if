import glob
import os
import subprocess

import dotbot
from dotbot.dispatcher import Dispatcher
from dotbot.util import module
from dotbot.plugins import Clean, Create, Link, Plugins, Shell


class If(dotbot.Plugin):
    _directive = 'if'

    def _load_plugins(self):        
        plugins = []
        plugin_directories = list(self._context.options().plugin_dirs)
        if not self._context.options().disable_built_in_plugins:
            plugins.extend([Clean, Create, Link, Plugins, Shell])
        plugin_paths = []
        for directory in plugin_directories:
            for plugin_path in glob.glob(os.path.join(directory, "*.py")):
                plugin_paths.append(plugin_path)
        for plugin_path in self._context.options().plugins:
            plugin_paths.append(plugin_path)
        for plugin_path in plugin_paths:
            abspath = os.path.abspath(plugin_path)
            plugins.extend(module.load(abspath))
        return plugins

    def can_handle(self, directive):
        return directive == self._directive

    def handle(self, directive, data):
        if directive != self._directive:
            raise ValueError(f'Cannot handle this directive {directive}')

        if isinstance(data, list):
            return all(self._handle_single_if(d) for d in data)

        return self._handle_single_if(data)

    def _handle_single_if(self, data):
        cond = data.get('cond')

        if not cond:
            raise ValueError('Missing "cond" parameter for "if" directive')
        if not isinstance(cond, str):
            raise ValueError('"cond" parameter must be a string')

        ret = subprocess.run(['bash', '-c', cond])
        is_met = ret.returncode == 0

        if (is_met and 'met' not in data) or (not is_met and 'unmet' not in data):
            return True

        return self._run_internal(data['met'] if is_met else data['unmet'])



    def _run_internal(self, data):
        dispatcher = Dispatcher(self._context.base_directory(),
                                only=self._context.options().only,
                                skip=self._context.options().skip,
                                options=self._context.options(),
                                plugins=self._load_plugins())
        return dispatcher.dispatch(data)
