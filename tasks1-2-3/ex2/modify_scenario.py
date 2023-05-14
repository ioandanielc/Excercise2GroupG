import argparse
import json
from pathlib import Path


def create_additional_pedestrian():
    """Creates a dictionary representing an additional pedestrian to be added to the scenario.

    Returns:
        A dictionary with keys representing the attributes of the pedestrian.
    """
    return {
        "attributes": {
            "id": 1,
            "shape": {
                "x": 0.0,
                "y": 0.0,
                "width": 1.0,
                "height": 1.0,
                "type": "RECTANGLE"
            },
            "visible": True,
            "radius": 0.2,
            "densityDependentSpeed": False,
            "speedDistributionMean": 1.34,
            "speedDistributionStandardDeviation": 0.26,
            "minimumSpeed": 0.5,
            "maximumSpeed": 2.2,
            "acceleration": 2.0,
            "footstepHistorySize": 4,
            "searchRadius": 1.0,
            "walkingDirectionSameIfAngleLessOrEqual": 45.0,
            "walkingDirectionCalculation": "BY_TARGET_CENTER"
        },
        "source": None,
        "targetIds": [2],
        "nextTargetListIndex": 0,
        "isCurrentTargetAnAgent": False,
        "position": {
            "x": 11.0,
            "y": 1.0
        },
        "velocity": {
            "x": 0.0,
            "y": 0.0
        },
        "freeFlowSpeed": 1.4648429039159518,
        "followers": [],
        "idAsTarget": -1,
        "isChild": False,
        "isLikelyInjured": False,
        "psychologyStatus": {
            "mostImportantStimulus": None,
            "threatMemory": {
                "allThreats": [],
                "latestThreatUnhandled": False
            },
            "selfCategory": "TARGET_ORIENTED",
            "groupMembership": "OUT_GROUP",
            "knowledgeBase": {
                "knowledge": [],
                "informationState": "NO_INFORMATION"
            },
            "perceivedStimuli": [],
            "nextPerceivedStimuli": []
        },
        "healthStatus": None,
        "infectionStatus": None,
        "groupIds": [],
        "groupSizes": [],
        "agentsInGroup": [],
        "trajectory": {
            "footSteps": []
        },
        "modelPedestrianMap": {},
        "type": "PEDESTRIAN"
    }


def main(args):
    """Modifies a Vadere scenario by adding an additional pedestrian.

    Args:
        args: An argparse.Namespace object containing parsed command-line arguments.

    Returns:
        None.
    """
    scenario_path = Path(args.scenario)
    save_path = Path(args.output) if args.output else scenario_path.with_name('modified.scenario')

    with scenario_path.open() as f:
        scenario = json.load(f)

    scenario["name"] = f"{scenario['name']}_modified"
    additional_pedestrian = create_additional_pedestrian()
    scenario['scenario']['topography']['dynamicElements'].append(additional_pedestrian)

    with save_path.open('w') as f:
        json.dump(scenario, f, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', help='path to the scenario JSON file',
                        default='/home/a_yaroshevich/projects/tum/vadere/Scenarios/Demos/bus_station/scenarios/scenario_2.scenario')
    parser.add_argument('--output', help='path to the output file (optional)')
    args = parser.parse_args()
    main(args)
