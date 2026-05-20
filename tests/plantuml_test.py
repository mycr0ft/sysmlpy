#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the PlantUML generator module.
"""

import pytest
import sysmlpy
from sysmlpy.plantuml import (
    to_plantuml,
    PlantUMLGenerator,
    _get_typedby_name,
    _get_specializes_names,
    _get_redefines_names,
)


class TestPlantUMLGenerator:
    """Tests for the PlantUML generator."""

    def test_basic_structure(self):
        """Test basic model generates valid PlantUML structure."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
            part def Vehicle {
                part frontLeft : Wheel;
            }
        }
        """)
        puml = to_plantuml(model)

        assert "@startuml" in puml
        assert "@enduml" in puml
        assert "Wheel" in puml
        assert "Vehicle" in puml
        assert "frontLeft" in puml

    def test_typing_relationship(self):
        """Test that typing relationships are generated."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
            part def Vehicle {
                part frontLeft : Wheel;
            }
        }
        """)
        puml = to_plantuml(model)

        assert "--:|>" in puml  # typing arrow
        assert "types" in puml

    def test_specialization_relationship(self):
        """Test that specialization relationships are generated."""
        model = sysmlpy.loads("""
        package P {
            part def RotatingPart;
            part def Wheel :> RotatingPart;
        }
        """)
        puml = to_plantuml(model)

        assert "--|>" in puml  # specialization arrow
        assert "specializes" in puml

    def test_redefinition_relationship(self):
        """Test that redefinition relationships are generated."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel {
                attribute radius;
            }
            part def CarWheel :> Wheel {
                attribute :>> radius;
            }
        }
        """)
        puml = to_plantuml(model)

        assert "--||>" in puml  # redefinition arrow
        assert "redefines" in puml

    def test_composite_containment(self):
        """Test that composite containment is generated."""
        model = sysmlpy.loads("""
        package P {
            part def Vehicle {
                part engine;
                part wheel;
            }
        }
        """)
        puml = to_plantuml(model)

        assert "*--" in puml  # composite diamond

    def test_bw_style(self):
        """Test B&W style generates monochrome output."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
        }
        """)
        puml = to_plantuml(model, style="bw")

        assert "skinparam monochrome true" in puml
        assert "<style>" not in puml  # No CSS block in BW mode

    def test_color_style(self):
        """Test color style generates CSS block."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
        }
        """)
        puml = to_plantuml(model, style="color")

        assert "<style>" in puml
        assert "RoundCorner" in puml

    def test_legend_included(self):
        """Test that legend is included by default."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
        }
        """)
        puml = to_plantuml(model, include_legend=True)

        assert "legend right" in puml
        assert "endlegend" in puml

    def test_legend_excluded(self):
        """Test that legend can be excluded."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
        }
        """)
        puml = to_plantuml(model, include_legend=False)

        assert "legend right" not in puml
        assert "endlegend" not in puml

    def test_direction_lr(self):
        """Test left-to-right direction."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
        }
        """)
        puml = to_plantuml(model, direction="LR")

        assert "left to right direction" in puml

    def test_direction_tb(self):
        """Test top-to-bottom direction."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
        }
        """)
        puml = to_plantuml(model, direction="TB")

        assert "top to bottom direction" in puml

    def test_stereotype_for_definition(self):
        """Test that definitions get correct stereotype."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
        }
        """)
        puml = to_plantuml(model)

        assert "part def" in puml

    def test_stereotype_for_usage(self):
        """Test that usages get correct stereotype."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
            part def Vehicle {
                part frontLeft : Wheel;
            }
        }
        """)
        puml = to_plantuml(model)

        # frontLeft is a usage, should have "part" stereotype (not "part def")
        assert "part>>" in puml
        assert "part def>>" in puml  # Wheel and Vehicle are definitions

    def test_multiple_relationships(self):
        """Test complex model with multiple relationship types."""
        model = sysmlpy.loads("""
        package Vehicle {
            part def RotatingPart;
            part def Wheel :> RotatingPart {
                attribute radius;
            }
            part def CarWheel :> Wheel {
                attribute :>> radius;
            }
            part def Vehicle {
                part frontLeft : CarWheel;
                part frontRight : CarWheel;
            }
        }
        """)
        puml = to_plantuml(model)

        # Check all relationship types present
        assert "--:|>" in puml  # typing
        assert "--|>" in puml   # specialization
        assert "--||>" in puml  # redefinition
        assert "*--" in puml    # composite containment

    def test_empty_model(self):
        """Test empty package generates valid PlantUML."""
        model = sysmlpy.loads("""
        package P {
        }
        """)
        puml = to_plantuml(model)

        assert "@startuml" in puml
        assert "@enduml" in puml


class TestHelperFunctions:
    """Tests for helper functions that extract relationships from grammar."""

    def test_get_typedby_name(self):
        """Test extracting typed-by name from grammar."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
            part def Vehicle {
                part frontLeft : Wheel;
            }
        }
        """)
        frontLeft = model.find('frontLeft')[0]
        name = _get_typedby_name(frontLeft)
        assert name == 'Wheel'

    def test_get_typedby_name_no_typing(self):
        """Test extracting typed-by name when no typing exists."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
        }
        """)
        wheel = model.find('Wheel')[0]
        name = _get_typedby_name(wheel)
        assert name is None

    def test_get_specializes_names(self):
        """Test extracting specialization names from grammar."""
        model = sysmlpy.loads("""
        package P {
            part def RotatingPart;
            part def Wheel :> RotatingPart;
        }
        """)
        wheel = model.find('Wheel')[0]
        names = _get_specializes_names(wheel)
        assert names == ['RotatingPart']

    def test_get_specializes_names_no_specialization(self):
        """Test extracting specialization names when none exist."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
        }
        """)
        wheel = model.find('Wheel')[0]
        names = _get_specializes_names(wheel)
        assert names == []

    def test_get_redefines_names(self):
        """Test extracting redefinition names from grammar."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel {
                attribute radius;
            }
            part def CarWheel :> Wheel {
                attribute :>> radius;
            }
        }
        """)
        carwheel = model.find('CarWheel')[0]
        # Find the anonymous redefining attribute
        for child in carwheel.children:
            names = _get_redefines_names(child)
            if names:
                assert 'radius' in names
                break

    def test_get_redefines_names_no_redefinition(self):
        """Test extracting redefinition names when none exist."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel {
                attribute radius;
            }
        }
        """)
        wheel = model.find('Wheel')[0]
        radius = wheel.children[0]
        names = _get_redefines_names(radius)
        assert names == []


class TestPlantUMLFiltering:
    """Tests for the focus/elements filtering features."""

    def test_focus_element(self):
        """Test focusing on a specific element shows only its subtree."""
        model = sysmlpy.loads("""
        package P {
            part def Vehicle {
                part engine;
                part wheel;
            }
            part def OtherThing {
                part something;
            }
        }
        """)
        vehicle = model.find('Vehicle')[0]
        puml = to_plantuml(model, focus=vehicle)

        assert "Vehicle" in puml
        assert "engine" in puml
        assert "wheel" in puml
        assert "OtherThing" not in puml
        assert "something" not in puml

    def test_focus_with_external_relationships(self):
        """Test that external relationships are shown when show_external=True."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
            part def Vehicle {
                part frontLeft : Wheel;
            }
        }
        """)
        vehicle = model.find('Vehicle')[0]
        puml = to_plantuml(model, focus=vehicle, show_external=True)

        # Should include Wheel (external) and the typing relationship
        assert "Wheel" in puml
        assert "--:|>" in puml
        assert "types" in puml

    def test_focus_without_external_relationships(self):
        """Test that external relationships are hidden when show_external=False."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
            part def Vehicle {
                part frontLeft : Wheel;
            }
        }
        """)
        vehicle = model.find('Vehicle')[0]
        puml = to_plantuml(model, focus=vehicle, show_external=False, include_legend=False)

        # Should NOT include Wheel or typing relationship
        assert "Wheel" not in puml
        # Check that no typing arrows appear in relationships (not in legend)
        lines = [l for l in puml.split('\n') if not l.strip().startswith('|')]
        rel_lines = [l for l in lines if '--:|>' in l]
        assert len(rel_lines) == 0

    def test_elements_filter(self):
        """Test selecting specific elements."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
            part def Axle;
            part def Engine;
        }
        """)
        wheel = model.find('Wheel')[0]
        axle = model.find('Axle')[0]
        puml = to_plantuml(model, elements=[wheel, axle])

        assert "Wheel" in puml
        assert "Axle" in puml
        assert "Engine" not in puml

    def test_elements_filter_shows_relationships(self):
        """Test that relationships between selected elements are shown."""
        model = sysmlpy.loads("""
        package P {
            part def RotatingPart;
            part def Wheel :> RotatingPart;
            part def Engine;
        }
        """)
        wheel = model.find('Wheel')[0]
        rotating = model.find('RotatingPart')[0]
        puml = to_plantuml(model, elements=[wheel, rotating])

        assert "Wheel" in puml
        assert "RotatingPart" in puml
        assert "--|>" in puml  # specialization
        assert "Engine" not in puml

    def test_max_depth(self):
        """Test max_depth limits traversal depth."""
        model = sysmlpy.loads("""
        package P {
            part def Vehicle {
                part engine {
                    part piston;
                }
            }
        }
        """)
        vehicle = model.find('Vehicle')[0]

        # max_depth=1 should only show Vehicle and engine
        puml = to_plantuml(model, focus=vehicle, max_depth=1)
        assert "Vehicle" in puml
        assert "engine" in puml
        assert "piston" not in puml

        # max_depth=2 should show all three
        puml = to_plantuml(model, focus=vehicle, max_depth=2)
        assert "Vehicle" in puml
        assert "engine" in puml
        assert "piston" in puml

    def test_focus_title(self):
        """Test that focus element name appears in title."""
        model = sysmlpy.loads("""
        package P {
            part def Vehicle;
        }
        """)
        vehicle = model.find('Vehicle')[0]
        puml = to_plantuml(model, focus=vehicle)

        assert "Vehicle" in puml.split('title')[1].split('\n')[0]

    def test_elements_title(self):
        """Test that element count appears in title."""
        model = sysmlpy.loads("""
        package P {
            part def Wheel;
            part def Axle;
        }
        """)
        wheel = model.find('Wheel')[0]
        axle = model.find('Axle')[0]
        puml = to_plantuml(model, elements=[wheel, axle])

        assert "Selected Elements (2)" in puml
