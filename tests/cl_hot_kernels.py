import os
import subprocess
import sys

import cl_gemm
import dpc_gemm
import omp_gemm
import utils

def config(path):
  p = subprocess.Popen(["cmake",\
    "-DCMAKE_BUILD_TYPE=" + utils.get_build_flag(), ".."],\
    cwd = path, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
  p.wait()
  stdout, stderr = utils.run_process(p)
  if stderr and stderr.find("CMake Error") != -1:
    return stderr
  return None

def build(path):
  p = subprocess.Popen(["make"], cwd = path,\
    stdout = subprocess.PIPE, stderr = subprocess.PIPE)
  p.wait()
  stdout, stderr = utils.run_process(p)
  if stderr and stderr.lower().find("error") != -1:
    return stderr
  return None

def parse(output):
  lines = output.split("\n")
  total_time = 0.0
  for line in lines:
    items = line.split("|")
    if len(items) < 8 or line.find("Kernel") != -1 or line.find("Call") != -1:
      continue
    kernel_name = items[1].strip()
    call_count = int(items[2].strip())
    time = float(items[6].strip())
    if not kernel_name or call_count <= 0:
      return False
    total_time += time
  if total_time <= 0:
    return False
  return True

def run(path, option):
  if option == "dpc":
    app_folder = utils.get_sample_build_path("dpc_gemm")
    app_file = os.path.join(app_folder, "dpc_gemm")
    option = "cpu"
  elif option == "omp":
    app_folder = utils.get_sample_build_path("omp_gemm")
    app_file = os.path.join(app_folder, "omp_gemm")
    option = "gpu"
  else:
    app_folder = utils.get_sample_build_path("cl_gemm")
    app_file = os.path.join(app_folder, "cl_gemm")
  p = subprocess.Popen(["./cl_hot_kernels", app_file, option, "1024", "1"],\
    cwd = path, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
  stdout, stderr = utils.run_process(p)
  if stderr:
    return stderr
  if stdout.find(" CORRECT") == -1:
    return stdout
  if stdout.find("Job is successfully completed") == -1:
    return stdout
  if not parse(stdout):
    return stdout
  return None

def main(option):
  path = utils.get_sample_build_path("cl_hot_kernels")
  if option == "dpc":
    log = dpc_gemm.main("cpu")
    if log:
      return log
  elif option == "omp":
    log = omp_gemm.main("gpu")
    if log:
      return log
  else:
    log = cl_gemm.main(option)
    if log:
      return log
  log = config(path)
  if log:
    return log
  log = build(path)
  if log:
    return log
  log = run(path, option)
  if log:
    return log
  log = run(path, option)
  if log:
    return log

if __name__ == "__main__":
  option = "gpu"
  if len(sys.argv) > 1 and sys.argv[1] == "cpu":
    option = "cpu"
  if len(sys.argv) > 1 and sys.argv[1] == "dpc":
    option = "dpc"
  if len(sys.argv) > 1 and sys.argv[1] == "omp":
    option = "omp"
  log = main(option)
  if log:
    print(log)