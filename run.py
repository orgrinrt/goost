#!/usr/bin/python3

import os
import sys
import argparse
import subprocess


def get_engine_executable_path():
    import json
    binary_path = ""
    try:
        with open("godot/.scons_env.json", "r") as f:
            env = json.load(f)
            if env["platform"] == "server":
                binary_path = "godot/bin/godot_server" + env["PROGSUFFIX"]
            else:
                binary_path = "godot/bin/godot" + env["PROGSUFFIX"]
    except OSError as e:
        print(e)
    if not binary_path:
        raise ValueError("No engine construction environment found.")
    return binary_path


def run(p_args, windowed=False, verbose=False): # Assumes the first arg is the binary path.
    args = p_args.copy()
    if not windowed:
        args.insert(1, "--no-window")
    if verbose:
        args.insert(1, "--verbose")
    return subprocess.run(args).returncode


if __name__ == "__main__":
    if not os.path.exists("godot"):
        print("Error: no Godot repository found at Goost root, aborting.")
        print("Please run `scons` command first.")
        sys.exit(255)

    base_path = os.path.dirname(os.path.abspath(__file__))
    try:
        godot_bin = get_engine_executable_path()
        if not os.path.exists(godot_bin):
            raise RuntimeError("Could not find engine executable.")
    except (ValueError, RuntimeError) as e:
        print("Error: %s" % e)
        print("Please run `scons` command first.")
        sys.exit(255)

    parser = argparse.ArgumentParser()
    parser.add_argument("--windowed", action="store_true", default=False, help="Run in windowed mode.")
    parser.add_argument("--verbose", action="store_true", default=False, help="Run in verbose mode.")
    parser.add_argument("--debug", action="store_true", default=False, help="Run in debug mode.")

    subparsers = parser.add_subparsers(dest="tool", required=True)

    # Editor.
    editor = subparsers.add_parser("editor", help="Run Godot editor.")
    
    # Unit tests.
    tests = subparsers.add_parser("tests", help="Run Goost unit tests (run with `tests -h` for more options).")
    tests.add_argument("-t", "--test-file",
            help='A relative path to test file to run, for instance: "core/math/test_random.gd"')
    tests.add_argument("-tc", "--test-case",
            help="Name of a test case to run. Any test case matching the name will be run.")

    # Documentation.
    doc = subparsers.add_parser("doc", help="Generate documentation.")

    # Parse!
    args = parser.parse_args()

    if args.tool.startswith("editor"):
        print("Running Godot editor ...")
        ret = run([godot_bin, "--path", "tests/project", "--editor"], windowed=True, verbose=args.verbose)
        sys.exit(ret)

    elif args.tool.startswith("test"):
        print("Running Goost tests ...")

        import atexit
        import time

        time_start = time.time()

        def print_time_elapsed():
            time_elapsed_sec = round(time.time() - time_start, 3)
            time_ms = round((time_elapsed_sec % 1) * 1000)
            print(f"[Time elapsed: {time.strftime('%H:%M:%S', time.gmtime(time_elapsed_sec))}.{time_ms:03}]")

        atexit.register(print_time_elapsed)

        test_args = [godot_bin]
        # Path to GUT test project.
        test_args.extend(["--path", "tests/project"])
        # Allows to speed up tests. Do not set below 15, may cause delta time errors.
        test_args.extend(["--fixed-fps", "15"])
        # Run in debug mode, disabling it allows to workaround:
        # https://github.com/godotengine/godot/issues/51387
        if args.debug:
            test_args.append("-d") # Use short options, GUT will break otherwise.
        # Path to GUT command-line script.
        test_args.extend(["-s", os.path.join(base_path, "tests/project/addons/gut/gut_cmdln.gd")])

        if args.test_file:
            # Reset `-gdir`, otherwise all scripts are going to be collected
            # recursively from the directory defined in `.gutconfig.json`.
            res_file = "res://goost/" + args.test_file
            test_args.extend(["-gtest=%s" % res_file, '-gdir='])
        if args.test_case:
            test_args.append("-gunit_test_name=%s" % args.test_case)
        if not args.windowed:
            # Not exiting on failure only makes sense while running in
            # windowed mode, this does not matter for console output.
            test_args.append("-gexit=true")

        try:
            ret = run(test_args, windowed=args.windowed, verbose=args.verbose)
            sys.exit(ret)
        except KeyboardInterrupt:
            print("Aborting Goost tests.")
            sys.exit(255)

    elif args.tool.startswith("doc"):
        print("Generating documentation ...")
        if not os.path.exists("doc/godot"):
            os.makedirs("doc/godot")
        ret = run([godot_bin, "--doctool", os.path.join(base_path, "doc/godot")],
                windowed=args.windowed, verbose=args.verbose)
        sys.exit(ret)
    else:
        print('Error: tool not found. Run with `--help` to list available tools.')
