import pytest
import unittest
import json
import wapi_module
import re
import time
import util
import os
from netaddr import IPNetwork

flavor_name = 'custom.flavor'
CPU = 2
RAM = '1024'
DISK = '10'

class TestOpenStackCases(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        pass

    @pytest.mark.run(order=1)
    def test_get_flavor_list(self):
	proc = util.utils()
	proc.flavor_create(flavor_name,CPU,RAM,DISK)
	flavors = proc.flavor_get(flavor_name)
	assert flavors == flavor_name
