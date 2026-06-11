#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 22:49:00 2023

@author: mycr0ft
"""

import pytest


@pytest.fixture
def single_package():
    return """package;"""
