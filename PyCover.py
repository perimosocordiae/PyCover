from __future__ import print_function
import os
import sublime
import sublime_plugin
import subprocess
import sys
import time
import threading

SETTINGS = None


def plugin_loaded():
  global SETTINGS
  SETTINGS = sublime.load_settings('PyCover.sublime-settings')
  if SETTINGS and SETTINGS.get('python') is not None:
    print('Loaded settings for PyCover')
  else:
    print('Error loading settings for PyCover')

if sys.version_info[0] == 2:
  sublime.set_timeout(plugin_loaded, 0)


class SublimePythonCoverageListener(sublime_plugin.EventListener):
  """Event listener to highlight uncovered lines when a Python file loads."""

  def on_load(self, view):
    if SETTINGS.get('onload', False) and 'source.python' in view.scope_name(0):
      view.run_command('show_python_coverage')


class ShowPythonCoverageCommand(sublime_plugin.TextCommand):
  """Highlight uncovered lines in the current file
  based on a previous coverage run."""

  def is_visible(self):
    return self.is_enabled()

  def is_enabled(self):
    return 'source.python' in self.view.scope_name(0)

  def run(self, edit):
    fname = self.view.file_name()
    if not self.is_enabled() or not fname:
      return

    local_settings = self.view.settings()
    if local_settings.get('showing', False):
      self.view.erase_regions('PyCover')
      local_settings.set('showing', False)
      return  # Toggle off

    cov_file = find(fname, '.coverage')
    if not cov_file:
      sublime.set_timeout(
          lambda: sublime.status_message('Could not find .coverage file'), 0)
      print('PyCover: Could not find .coverage file for', fname)
      return
    cov_config = find(fname, '.coveragerc') or ''

    # run missing_lines.py with the correct paths
    python = SETTINGS.get('python', '')
    if not python:
      python = which('python')
    ml_file = os.path.join(os.path.dirname(__file__), 'scripts',
                           'missing_lines.py')
    p = subprocess.Popen([python, ml_file, cov_file, cov_config, fname],
                         stdout=subprocess.PIPE)
    threading.Thread(target=missing_lines_callback, args=(self.view, p)).start()


def missing_lines_callback(view, proc, poll_sleep=0.1, poll_timeout=10):
  progress_status = lambda: sublime.status_message('Finding missing lines...')
  sublime.set_timeout(progress_status, 0)
  # poll for results
  tic = time.time()
  while proc.poll() is None:
    if time.time() - tic > poll_timeout:
      msg = 'missing_lines.py timed out after %f s' % (time.time() - tic)
      print(msg)
      sublime.set_timeout(lambda: sublime.status_message(msg), 0)
      proc.kill()
      return
    time.sleep(poll_sleep)
    sublime.set_timeout(progress_status, 0)

  # read stdout to parse missing lines
  stdout, _ = proc.communicate()
  missing_lines = map(int, stdout.decode('UTF-8').splitlines())

  # update highlighted regions
  sublime.set_timeout(lambda: _update_highlighted(view, missing_lines), 0)


def _update_highlighted(view, missing_lines):
  outlines = [
      view.full_line(view.text_point(line_num-1, 0))
      for line_num in missing_lines]
  view.erase_regions('PyCover')
  if outlines:
    view.add_regions('PyCover', outlines, 'markup.inserted',
                     'bookmark', sublime.HIDDEN)
    view.settings().set('showing', True)
  msg = '%d missing lines annotated.' % len(outlines)
  print(msg)
  sublime.status_message(msg)


def find(base, *rel, **kwargs):
  access = kwargs.get('access', os.R_OK)
  rel = os.path.join(*rel)
  while True:
    path = os.path.join(base, rel)
    if os.access(path, access):
      return path
    baseprev, base = base, os.path.dirname(base)
    if not base or base == baseprev:
      return


def which(progname):
  exts = os.environ.get('PATHEXT', '').split(os.pathsep)
  for path in os.environ['PATH'].split(os.pathsep):
    for ext in exts:
      fullpath = os.path.join(path, progname + ext)
      if os.path.exists(fullpath):
        return fullpath
  return None
