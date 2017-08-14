from __future__ import print_function
import sys
from coverage import coverage


def missing_lines(cov_file, cov_config, fname):
  cov = coverage(data_file=cov_file, config_file=cov_config)
  cov.load()
  if cov.omit_match and cov.omit_match.match(fname):
    sys.stderr.write('Omitted file.\n')
    sys.exit(1)

  missing_lines = cov.analysis(fname)[2]
  print(*missing_lines, sep='\n', end='')

if __name__ == '__main__':
  missing_lines(*sys.argv[1:])
