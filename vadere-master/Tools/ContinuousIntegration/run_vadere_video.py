# Use "vadere-video.jar" and "vadere-console.jar" which is created by "mvn package", to generate videos.
# scenario files under "Scenarios/ModelTests" subdirectory.
#
# Note: script contains some print statements so that progress can be tracked
# a little bit while script is running in continuous integration pipeline.

# Watch out: call this script from root directory of project. E.g.
#
#   python Tools/my_script.py

import argparse
import glob
import os
import shutil
import subprocess

import run_vadere_console_with_all_scenario_files as rv

max_time_for_video_gen_in_secs = 600 #tem minutes


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description="Generate a video from each Vadere output available in a directory.")

    parser.add_argument("--scenarios-specified-in-config-only",
                        dest="run_all_scenarios_in_dir",
                        action='store_false',
                        default=True,
                        help="Only has an effect if -d is set. "
                        )

    parser.add_argument("-i",
                        dest="output_dir",
                        type=str,
                        nargs="?",
                        help="Generate video for the given vadere output and not all. E.g., Scenarios/ModelTests/",
                        default="SimulationOutput")

    parser.add_argument("-o",
                        dest="video_dir",
                        type=str,
                        help="Store videos in this folder.",
                        default="VideoOutput",
                        nargs="?", )

    parser.add_argument("-d",
                        dest="scenario_dir",
                        type=str,
                        help="Folder that contains vadere projects or scenarios. "
                             "The contained scenarios to produce simulation output for the video generation."
                             "Set the --all",
                        default=None,
                        nargs="?", )

    return parser.parse_args()


def get_map_output_video(dir_containing_vadere_output):
    dir_containing_vadere_output = os.path.abspath(dir_containing_vadere_output)
    output_video = dict()

    for traj_file in glob.glob(f'{dir_containing_vadere_output}/**/postvis.traj', recursive=True):
        output_dir = os.path.dirname(traj_file)
        if "corrupt" in output_dir.split(os.sep):
            print(f"Do not proceed corrupt output found in {output_dir}")
        else:
            is_vadere_output_dir(output_dir)
            video_name = f"{os.path.basename(output_dir)}.mov"
            rel_path = os.path.relpath(output_dir, dir_containing_vadere_output)
            video_name = os.path.join(os.path.dirname(rel_path), video_name)
            output_video[output_dir] = video_name

    return output_video


def is_vadere_output_dir(output_dir):

    scenario_file = glob.glob(f"{output_dir}/*.scenario")
    traj_file = glob.glob(f"{output_dir}/postvis.traj")
    if len(scenario_file) == 1:
        scenario_file = scenario_file[0]
    else:
        raise ValueError(
            f"Output directory (={output_dir}) must contain one *.scenario file. Got {len(scenario_file)} scenario files.")
    if len(traj_file) == 1:
        traj_file = traj_file[0]
    else:
        raise ValueError(
            f"Output directory (={output_dir}) must contain one *.scenario file. Got {len(traj_file)} scenario files.")
    return scenario_file


def generate_videos(vadere_output_dirs, vadere_video="VadereGui/target/vadere-video.jar", scenario_timeout_in_sec=200,
                    video_path="VideoFiles"):

    log_base_dir = "vadere_logs"
    rv.makedirs_if_non_existing(log_base_dir)

    passed_videos = list()
    failed_videos_with_exception = list()
    failed_summary = list()

    video_file_path = os.path.abspath(video_path)

    if os.path.exists(video_file_path):
        shutil.rmtree(video_file_path)
    os.makedirs(video_file_path)

    for vadere_output, video_name in vadere_output_dirs.items():

        try:
            print(f"Generate video from simulation output found in {vadere_output}")

            vadere_output = os.path.abspath(vadere_output)

            dir_name = os.path.join(video_file_path, os.path.dirname(video_name))
            if os.path.exists(dir_name) == False:
                os.makedirs(dir_name)

            log_file = f"{os.path.splitext(os.path.basename(video_name))[0]}-VIDEO-GENERATION.log"

            log_file = os.path.join(".", log_base_dir, log_file)

            # print("  Log file: " + log_file) #TODO use log file (currently not working)

            video_name_path = os.path.join(video_file_path, video_name)

            # Build subprocess args:
            # Basic, always enable asserttions for tests
            subprocess_args = ["java",
                               "-enableassertions",
                               "-jar", vadere_video,
                               "--logname", log_file #TODO use log file (currently not working)
                               ]
            # add config file if required

            # run per vadere output directory
            subprocess_args += ["-i", vadere_output]
            subprocess_args += ["-o", video_name_path]

            # Use timout feature, check return value and capture stdout/stderr to a PIPE (use completed_process.stdout
            # to get it).
            completed_process = subprocess.run(args=subprocess_args,
                                               timeout=max_time_for_video_gen_in_secs,
                                               check=True,
                                               stdout=subprocess.PIPE, #TODO use log file
                                               stderr=subprocess.PIPE
                                               )

            print(f"Finished video {video_name_path}.")
            passed_videos.append(video_name_path)

        except subprocess.TimeoutExpired as exception:
            print(f"Could not produce video from vadere output {vadere_output}.")
            print("->  Reason: timeout after {} s".format(exception.timeout))
            failed_videos_with_exception.append((vadere_output, exception))

        except subprocess.CalledProcessError as exception:
            print(f"Video generation failed for vadere output {vadere_output}")
            print(f"->  Reason: non-zero return value {exception.returncode}")
            print(f"           {exception.stderr}")
            failed_videos_with_exception.append((vadere_output, exception))

            failed_summary.append(f"Video generation failed for vadere output {vadere_output}")
            failed_summary.append(f"->  Reason: non-zero return value {exception.returncode}")
            failed_summary.append(f"           {exception.stderr}")

    return result_dict_create(passed_videos, failed_videos_with_exception, failed_summary)


def result_dict_create(passed, failed, failed_summary):
    return {"passed": passed, "failed": failed, "failed_summary": failed_summary}


def result_dict_has_failed_tests(passed_and_failed_scenarios):
    return len(passed_and_failed_scenarios["failed"]) > 0


def result_dict_print_summary(passed_and_failed_scenarios):
    total_passed_scenarios = len(passed_and_failed_scenarios["passed"])
    total_failed_scenarios = len(passed_and_failed_scenarios["failed"])
    total_scenarios = total_passed_scenarios + total_failed_scenarios
    failed_summary = passed_and_failed_scenarios["failed_summary"]

    if result_dict_has_failed_tests(passed_and_failed_scenarios):
        print("")
        print("##################")
        print("# Failed Summary #")
        print("##################")
        for line in failed_summary:
            print(line)

    print("")
    print("###########")
    print("# Summary #")
    print("###########")
    print("")
    print("Total videos generated: {}".format(total_scenarios))
    print("Passed: {}".format(total_passed_scenarios))
    print("Failed: {}".format(total_failed_scenarios))


def find_scenarios(path=".", run_all=False):
    path_ = os.path.abspath(path)

    scenarios = list()

    if run_all:
        # find all scenario files
        scenarios = glob.glob(f'{path_}/**/*.scenario')
        scenarios = [s for s in scenarios if os.path.basename(os.path.dirname(s)) == "scenarios"]
    else:
        config_files = glob.glob(f'{path_}/**/VIDEO.config', recursive=True)

        for c in config_files:
            if os.path.basename(os.path.dirname(c)) != "scenarios":
                raise ValueError(f"VIDEO.config file must be stored in scenarios folder. Got: {c}.")

            with open(c) as f:
                config = f.read().splitlines()

            for line in config:
                scenario_list = glob.glob(f'{os.path.dirname(c)}/*{line}*')
                scenarios.extend(scenario_list)



    print(f"Try to run the {len(scenarios)} *.scenarios files:")
    for s in scenarios:
        print(s)

    return scenarios


if __name__ == "__main__":

    args = parse_command_line_arguments()

    if args.scenario_dir:
        is_specified_scenarios_only = args.run_all_scenarios_in_dir
        find_scenario_files_ = find_scenarios(path=args.scenario_dir, run_all=is_specified_scenarios_only)

        for f in find_scenario_files_:
            rel_path = os.path.dirname(os.path.dirname(os.path.relpath(f, args.scenario_dir)))
            outputdir_scenario = os.path.join(os.path.abspath(args.output_dir), rel_path)
            result = rv.run_scenario_files_with_vadere_console([f], output_dir= outputdir_scenario, is_keep_output=True)


    directories = get_map_output_video(dir_containing_vadere_output=args.output_dir)
    passed_and_failed_videos = generate_videos(directories, scenario_timeout_in_sec=100, video_path=args.video_dir)

    result_dict_print_summary(passed_and_failed_videos)

    if result_dict_has_failed_tests(passed_and_failed_videos):
        exit(1)
    else:
        exit(0)
