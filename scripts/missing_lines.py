from __future__ import print_function
import os
import sys
from coverage import coverage
from coverage.files import FnmatchMatcher


def missing_lines(cov_file, cov_config, fname):
  cov = coverage(data_file=cov_file, config_file=cov_config)
  if FnmatchMatcher(cov.omit).match(fname):
    return
  cov_dir = os.path.dirname(cov_file)
  relpath = os.path.relpath(fname, cov_dir)
  cov.load()
  missing_lines = cov.analysis(relpath)[2]
  for n in missing_lines:
    print(n)

if __name__ == '__main__':
  missing_lines(*sys.argv[1:])
