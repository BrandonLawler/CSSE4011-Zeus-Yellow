import logging
import os
import sys

from modules.core.core import Core
from src.app import App
from src.scoms import SComs
from src.influx import Api
from src.knn import KNN


def main():
    core = Core(log_level=logging.DEBUG, environment_json="files/environment.json", log_environment="CSSE4011-YZ-FP-LOGS")

    # Add multiprocessor functions
    core.create_class_process(os.getenv("CSSE4011-YZ-CN-SERIAL"), SComs)
    core.create_class_process(os.getenv("CSSE4011-YZ-CN-INFLUX"), Api)
    core.create_class_process(os.getenv("CSSE4011-YZ-CN-APPLICATION"), App)
    core.create_class_process(os.getenv("CSSE4011-YZ-CN-LEARNER"), KNN)

        # Check Startup Arguments
    if len(sys.argv) > 1:
        for argument in sys.argv[1:]:
            if argument == "--clear":
                check = input("This will delete all data are you sure you want to continue? (y/n) ").lower()
                if check == "y" or check == "yes":
                    core.send(os.getenv("CSSE4011-YZ-CN-INFLUX"), "clearTestData")

    core.start()


if __name__ == "__main__":
    main()