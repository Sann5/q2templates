# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import inspect
import os
import pkg_resources
import shutil
import tempfile

from .util import copy_assets, get_iterable
from jinja2 import Environment, FileSystemLoader, meta


def render(source_files, output_dir, context=None):
    """Render user provided source files into a QIIME 2 visualization template.


    Parameters
    ----------
    source_files : str, or list of str
        Files to be rendered and written to the output_dir.
    output_dir : str
        The output_dir provided to a visualiation function by the QIIME 2
        framework.
    context : dict, optional
        The context dictionary to be rendered into the source_files. The
        same context will be provided to all templates being rendered.

    """
    # Returns an iterable of paths (the provided html's).
    src = get_iterable(source_files)
    
    # TODO: Hook into qiime.sdk.config.TemporaryDirectory() when it exists
    
    # Create temp dir
    temp_dir = tempfile.TemporaryDirectory()
    
    # Gets path in system to dir "templates" from package "q2templates"
    template_data = pkg_resources.resource_filename('q2templates', 'templates')

    # Initialized jinja object with the temp dir path
    env = Environment(loader=FileSystemLoader(temp_dir.name), auto_reload=True)

    # Copies "template_data/base.html" to temp dir
    shutil.copy2(os.path.join(template_data, 'base.html'), temp_dir.name)

    # This loop parses each source file in search for referenced templates
    # When it finds them and they are not already in the temp dir it copies them
    # from template_data to temp dir
    for source_file in src:
        with open(source_file, 'r') as fh:
            ast = env.parse(fh.read())
        for template in list(meta.find_referenced_templates(ast)):
            if template not in os.listdir(temp_dir.name):
                shutil.copy2(os.path.join(template_data, template),
                             temp_dir.name)

    # If context was omited in the function call it asigns an empty dict
    if context is None:
        context = {}
    
    # Grab the plugin and visualizer method name for default titles (from tab in browser)
    stack = inspect.stack()
    caller_frame = stack[1]
    caller_filename = caller_frame[0]
    caller_module = inspect.getmodule(caller_filename)
    plugin = caller_module.__name__.split('.')[0]
    method = caller_frame[3]
    context['q2templates_default_page_title'] = '%s : %s' % (plugin, method)

    # Copy user files to the environment for rendering to the output_dir
    for source_file in src:
        shutil.copy2(source_file, temp_dir.name)
        filename = os.path.basename(source_file)
        template = env.get_template(filename)
        rendered_content = template.render(**context)
        with open(os.path.join(output_dir, filename), "w") as fh:
            fh.write(rendered_content)

    # Move the style assets to the output_dir
    template_assets = os.path.join(template_data, 'assets')
    output_assets = os.path.join(output_dir, 'q2templateassets')
    copy_assets(template_assets, output_assets)
