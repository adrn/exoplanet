#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import re
import sys

import nbformat
from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor

if len(sys.argv) >= 2:
    pattern = sys.argv[1]
else:
    pattern = "notebooks/*.ipynb"


filenames = [fn for fn in glob.glob(pattern) if not fn.endswith("_exec.ipynb")]
filenames = list(sorted(filenames, reverse=True))

num_files = len(filenames)
# cpu_count = multiprocessing.cpu_count()
# num_jobs = max(1, cpu_count // 4)
# print("Running on {0} CPUs".format(cpu_count))
# print("Running {0} jobs".format(num_jobs))


def process_notebook(filename):
    path = os.path.join(
        os.path.abspath("theano_cache"), "p{0}".format(os.getpid())
    )
    os.makedirs(path, exist_ok=True)
    os.environ["THEANO_FLAGS"] = "base_compiledir={0}".format(path)

    errors = []

    with open(filename) as f:
        notebook = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=-1)

    print("running: {0}".format(filename))
    try:
        ep.preprocess(notebook, {"metadata": {"path": "notebooks/"}})
    except CellExecutionError as e:
        msg = "error while running: {0}\n\n".format(filename)
        msg += e.traceback
        print(msg)
        errors.append(msg)
    finally:
        with open(os.path.join("_static", filename), mode="wt") as f:
            nbformat.write(notebook, f)

    return "\n\n".join(errors)


# with multiprocessing.Pool(num_jobs) as pool:
errors = list(map(process_notebook, filenames))

errors = [e for e in errors if len(e.strip())]
txt = "\n\n".join(errors)
ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
txt = ansi_escape.sub("", txt)

with open("notebook_errors.log", "wb") as f:
    f.write(txt.encode("utf-8"))
