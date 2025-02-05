#!/usr/bin/env python
import logging
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "back"))
    os.environ["DJANGO_SETTINGS_MODULE"] = "api.settings"
    django.setup()
    TestRunner = get_runner(settings)
    logging.disable(logging.CRITICAL)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["photo_objects.django.tests"])
    sys.exit(min(failures, 250))
