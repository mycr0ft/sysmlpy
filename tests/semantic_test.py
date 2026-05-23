#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for semantic analysis (undefined symbol detection)."""

import pytest
from sysmlpy import loads, analyze, SemanticIssue


class TestBasicUndefinedDetection:
    """Detect references to types that are not defined in the model."""

    def test_undefined_type_reference(self):
        model = loads("""
            package P {
                part x : UndefinedType;
            }
        """)
        issues = analyze(model)
        assert any(
            i.code == "UNDEFINED_SYMBOL" and "UndefinedType" in i.message
            for i in issues
        )

    def test_undefined_subsetting(self):
        model = loads("""
            package P {
                part x :> UndefinedFeature;
            }
        """)
        issues = analyze(model)
        assert any(
            i.code == "UNDEFINED_SYMBOL" and "UndefinedFeature" in i.message
            for i in issues
        )

    def test_undefined_redefinition(self):
        model = loads("""
            package P {
                part :>> UndefinedRedefined;
            }
        """)
        issues = analyze(model)
        assert any(
            i.code == "UNDEFINED_SYMBOL" and "UndefinedRedefined" in i.message
            for i in issues
        )


class TestDefinedNoFalsePositives:
    """References to defined types should NOT be flagged."""

    def test_defined_type_reference(self):
        model = loads("""
            package P {
                part def MyPart;
                part x : MyPart;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_part_def_used_by_part(self):
        model = loads("""
            package P {
                part def Engine;
                part myEngine : Engine;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_item_def_used_by_item(self):
        model = loads("""
            package P {
                item def Widget;
                item myWidget : Widget;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_port_def_used_by_port(self):
        model = loads("""
            package P {
                port def SensorPort;
                port p : SensorPort;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_attribute_def_used_by_attribute(self):
        model = loads("""
            package P {
                attribute def MyAttr;
                attribute a : MyAttr;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_action_def_used_by_action(self):
        model = loads("""
            package P {
                action def MyAction;
                action a : MyAction;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_state_def_used_by_state(self):
        model = loads("""
            package P {
                state def MyState;
                state s : MyState;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_constraint_def_used_by_constraint(self):
        model = loads("""
            package P {
                constraint def MyConstraint;
                constraint c : MyConstraint;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_calculation_def_used_by_calculation(self):
        model = loads("""
            package P {
                calc def MyCalc;
                calc c : MyCalc;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_requirement_def_used_by_requirement(self):
        model = loads("""
            package P {
                requirement def MyReq;
                requirement r : MyReq;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_interface_def_used_by_interface(self):
        model = loads("""
            package P {
                interface def MyInterface;
                interface i : MyInterface;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_connection_def_used_by_connection(self):
        model = loads("""
            package P {
                connection def MyConn;
                connection c : MyConn;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_enumeration_def_used_by_enum(self):
        model = loads("""
            package P {
                enum def MyEnum { A; B; }
                enum e : MyEnum;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)


class TestQualifiedNameResolution:
    """Package-qualified references should resolve correctly."""

    def test_cross_package_reference(self):
        model = loads("""
            package P {
                part def A;
            }
            package Q {
                part x : P::A;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_missing_package_reference(self):
        model = loads("""
            package Q {
                part x : P::A;
            }
        """)
        issues = analyze(model)
        assert any(
            i.code == "UNDEFINED_SYMBOL" and "P::A" in i.message
            for i in issues
        )

    def test_nested_package_reference(self):
        model = loads("""
            package Outer {
                package Inner {
                    part def DeepPart;
                }
                part x : Inner::DeepPart;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_deeply_nested_reference(self):
        model = loads("""
            package A {
                package B {
                    package C {
                        part def DeepPart;
                    }
                }
            }
            package X {
                part x : A::B::C::DeepPart;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)


class TestNestedScopeResolution:
    """References should resolve through parent scopes."""

    def test_child_references_parent_scope(self):
        model = loads("""
            package P {
                part def A;
                package Q {
                    part x : A;
                }
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_sibling_package_no_cross_ref(self):
        model = loads("""
            package P {
                package A {
                    part def PartA;
                }
                package B {
                    part x : PartA;
                }
            }
        """)
        issues = analyze(model)
        # PartA is defined in sibling package A, not directly visible in B
        # In SysML v2, sibling elements require qualified names or imports
        assert any(i.code == "UNDEFINED_SYMBOL" and "PartA" in i.message for i in issues)

    def test_sibling_package_with_qualified_name(self):
        model = loads("""
            package P {
                package A {
                    part def PartA;
                }
                package B {
                    part x : A::PartA;
                }
            }
        """)
        issues = analyze(model)
        # Qualified name should resolve correctly
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)


class TestMultipleUndefinedReferences:
    """Multiple undefined references should each produce an issue."""

    def test_three_undefined_types(self):
        model = loads("""
            package P {
                part a : TypeA;
                part b : TypeB;
                part c : TypeC;
            }
        """)
        issues = analyze(model)
        undefined = [i for i in issues if i.code == "UNDEFINED_SYMBOL"]
        assert len(undefined) == 3

    def test_mixed_defined_and_undefined(self):
        model = loads("""
            package P {
                part def Defined;
                part a : Defined;
                part b : Undefined;
            }
        """)
        issues = analyze(model)
        undefined = [i for i in issues if i.code == "UNDEFINED_SYMBOL"]
        assert len(undefined) == 1
        assert "Undefined" in undefined[0].message


class TestEmptyModel:
    """Empty models should produce no issues."""

    def test_empty_package(self):
        model = loads("""
            package Empty {}
        """)
        issues = analyze(model)
        assert len(issues) == 0

    def test_package_with_only_definitions(self):
        model = loads("""
            package P {
                part def A;
                part def B;
                item def C;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)


class TestSemanticIssueProperties:
    """Verify SemanticIssue dataclass fields."""

    def test_issue_has_required_fields(self):
        model = loads("""
            package P {
                part x : MissingType;
            }
        """)
        issues = analyze(model)
        issue = [i for i in issues if i.code == "UNDEFINED_SYMBOL"][0]
        assert issue.severity == "error"
        assert issue.code == "UNDEFINED_SYMBOL"
        assert "MissingType" in issue.message
        assert issue.reference == "MissingType"
        assert issue.element is not None


class TestLibrarySymbolWhitelist:
    """Standard library symbols should not be flagged as undefined."""

    def test_scalar_values_integer(self):
        model = loads("""
            package P {
                attribute mass : ScalarValues::Integer;
            }
        """)
        issues = analyze(model)
        assert not any(
            i.code == "UNDEFINED_SYMBOL" and "ScalarValues::Integer" in i.message
            for i in issues
        )

    def test_scalar_values_real(self):
        model = loads("""
            package P {
                attribute value : ScalarValues::Real;
            }
        """)
        issues = analyze(model)
        assert not any(
            i.code == "UNDEFINED_SYMBOL" and "ScalarValues::Real" in i.message
            for i in issues
        )

    def test_scalar_values_string(self):
        model = loads("""
            package P {
                attribute name : ScalarValues::String;
            }
        """)
        issues = analyze(model)
        assert not any(
            i.code == "UNDEFINED_SYMBOL" and "ScalarValues::String" in i.message
            for i in issues
        )

    def test_isq_length_value(self):
        model = loads("""
            package P {
                attribute length : ISQ::LengthValue;
            }
        """)
        issues = analyze(model)
        assert not any(
            i.code == "UNDEFINED_SYMBOL" and "ISQ::LengthValue" in i.message
            for i in issues
        )

    def test_isq_mass_value(self):
        model = loads("""
            package P {
                attribute mass : ISQ::MassValue;
            }
        """)
        issues = analyze(model)
        assert not any(
            i.code == "UNDEFINED_SYMBOL" and "ISQ::MassValue" in i.message
            for i in issues
        )

    def test_isq_force_value(self):
        model = loads("""
            package P {
                attribute force : ISQ::ForceValue;
            }
        """)
        issues = analyze(model)
        assert not any(
            i.code == "UNDEFINED_SYMBOL" and "ISQ::ForceValue" in i.message
            for i in issues
        )

    def test_isq_pressure_value(self):
        model = loads("""
            package P {
                attribute pressure : ISQ::PressureValue;
            }
        """)
        issues = analyze(model)
        assert not any(
            i.code == "UNDEFINED_SYMBOL" and "ISQ::PressureValue" in i.message
            for i in issues
        )


class TestImportResolution:
    """Import resolution should make imported symbols visible."""

    def test_namespace_import_makes_symbols_visible(self):
        model = loads("""
            package Types {
                part def Engine;
                part def Wheel;
            }
            package Vehicle {
                import Types::*;
                part myCar : Engine;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_membership_import_makes_symbol_visible(self):
        model = loads("""
            package Types {
                part def Engine;
            }
            package Vehicle {
                import Types::Engine;
                part myCar : Engine;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_import_without_wildcard(self):
        model = loads("""
            package Types {
                part def Engine;
                part def Wheel;
            }
            package Vehicle {
                import Types::Engine;
                part myCar : Engine;
                part myWheel : Wheel;
            }
        """)
        issues = analyze(model)
        # Engine is imported, Wheel is not
        undefined = [i for i in issues if i.code == "UNDEFINED_SYMBOL"]
        assert len(undefined) == 1
        assert "Wheel" in undefined[0].message

    def test_recursive_import(self):
        model = loads("""
            package Types {
                package Mechanical {
                    part def Engine;
                }
                package Electrical {
                    part def Motor;
                }
            }
            package Vehicle {
                import Types::*::**;
                part myCar : Engine;
                part myHybrid : Motor;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_unresolved_import_target(self):
        model = loads("""
            package Vehicle {
                import NonExistent::*;
                part myCar : SomeType;
            }
        """)
        issues = analyze(model)
        # SomeType is not defined or imported
        assert any(i.code == "UNDEFINED_SYMBOL" and "SomeType" in i.message for i in issues)

    def test_cross_package_import(self):
        model = loads("""
            package A {
                package B {
                    part def PartB;
                }
            }
            package C {
                import A::B::*;
                part x : PartB;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)


class TestUnresolvedImportDetection:
    """Import targets that don't exist should be flagged."""

    def test_import_from_nonexistent_package(self):
        model = loads("""
            package Vehicle {
                import NonExistent::*;
            }
        """)
        issues = analyze(model)
        assert any(
            i.code == "UNRESOLVED_IMPORT" and "NonExistent" in i.message
            for i in issues
        )

    def test_import_specific_nonexistent_element(self):
        model = loads("""
            package Vehicle {
                import NonExistent::Engine;
            }
        """)
        issues = analyze(model)
        assert any(
            i.code == "UNRESOLVED_IMPORT" and "NonExistent::Engine" in i.message
            for i in issues
        )

    def test_import_from_nested_nonexistent_package(self):
        model = loads("""
            package A {
                package B {
                    part def PartB;
                }
            }
            package C {
                import A::NonExistent::*;
            }
        """)
        issues = analyze(model)
        assert any(
            i.code == "UNRESOLVED_IMPORT" and "A::NonExistent" in i.message
            for i in issues
        )

    def test_valid_import_not_flagged(self):
        model = loads("""
            package Types {
                part def Engine;
            }
            package Vehicle {
                import Types::*;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNRESOLVED_IMPORT" for i in issues)

    def test_valid_membership_import_not_flagged(self):
        model = loads("""
            package Types {
                part def Engine;
            }
            package Vehicle {
                import Types::Engine;
            }
        """)
        issues = analyze(model)
        assert not any(i.code == "UNRESOLVED_IMPORT" for i in issues)

    def test_unresolved_import_and_undefined_symbol_both_reported(self):
        model = loads("""
            package Vehicle {
                import NonExistent::*;
                part myCar : SomeType;
            }
        """)
        issues = analyze(model)
        assert any(i.code == "UNRESOLVED_IMPORT" for i in issues)
        assert any(i.code == "UNDEFINED_SYMBOL" for i in issues)

    def test_recursive_import_from_nonexistent(self):
        model = loads("""
            package Vehicle {
                import NonExistent::*::**;
            }
        """)
        issues = analyze(model)
        assert any(
            i.code == "UNRESOLVED_IMPORT" and "NonExistent" in i.message
            for i in issues
        )


class TestSubsettingResolution:
    """Subsetting references should resolve to defined features, including inherited ones."""

    def test_subsetting_to_defined_feature(self):
        model = loads("""
            package P {
                part def Base {
                    attribute baseAttr;
                }
                part def Derived :> Base {
                    attribute myAttr :> baseAttr;
                }
            }
        """)
        issues = analyze(model)
        # baseAttr is inherited from Base - should resolve correctly
        assert not any(i.code == "UNDEFINED_SYMBOL" and "baseAttr" in i.message for i in issues)

    def test_subsetting_to_undefined_feature(self):
        model = loads("""
            package P {
                part def Base {
                    attribute baseAttr;
                }
                part def Derived :> Base {
                    attribute myAttr :> nonexistent;
                }
            }
        """)
        issues = analyze(model)
        # nonexistent is not defined in Base or Derived
        assert any(i.code == "UNDEFINED_SYMBOL" and "nonexistent" in i.message for i in issues)

    def test_subsetting_through_multiple_inheritance_levels(self):
        model = loads("""
            package P {
                part def Root {
                    attribute rootAttr;
                }
                part def Middle :> Root {
                    attribute middleAttr;
                }
                part def Leaf :> Middle {
                    attribute leafAttr1 :> rootAttr;
                    attribute leafAttr2 :> middleAttr;
                }
            }
        """)
        issues = analyze(model)
        # Both rootAttr and middleAttr should resolve through inheritance chain
        assert not any(i.code == "UNDEFINED_SYMBOL" for i in issues)


class TestConvenienceFunction:
    """The module-level analyze() function should work."""

    def test_analyze_returns_list(self):
        model = loads("package P {}")
        result = analyze(model)
        assert isinstance(result, list)

    def test_analyze_finds_issues(self):
        model = loads("""
            package P {
                part x : MissingType;
            }
        """)
        result = analyze(model)
        assert len(result) > 0


class TestLibrarySymbolIndex:
    """Verify library symbol loading from .kerml/.sysml files."""

    def test_library_index_returns_nonempty(self):
        from sysmlpy.semantic import LibrarySymbolIndex
        symbols = LibrarySymbolIndex.get_symbols()
        assert len(symbols) > 0

    def test_library_contains_scalar_values(self):
        from sysmlpy.semantic import LibrarySymbolIndex
        symbols = LibrarySymbolIndex.get_symbols()
        assert "ScalarValues::Integer" in symbols
        assert "ScalarValues::Real" in symbols
        assert "ScalarValues::String" in symbols
        assert "ScalarValues::Boolean" in symbols

    def test_library_contains_isq_types(self):
        from sysmlpy.semantic import LibrarySymbolIndex
        symbols = LibrarySymbolIndex.get_symbols()
        assert "ISQBase::LengthValue" in symbols
        assert "ISQBase::MassValue" in symbols
        assert "ISQBase::DurationValue" in symbols

    def test_library_contains_kerml_types(self):
        from sysmlpy.semantic import LibrarySymbolIndex
        symbols = LibrarySymbolIndex.get_symbols()
        assert "KerML::Kernel::Class" in symbols
        assert "KerML::Core::Classifier" in symbols
        assert "KerML::Kernel::Association" in symbols

    def test_library_contains_collections(self):
        from sysmlpy.semantic import LibrarySymbolIndex
        symbols = LibrarySymbolIndex.get_symbols()
        assert "Collections::Collection" in symbols

    def test_library_cache_is_reused(self):
        from sysmlpy.semantic import LibrarySymbolIndex
        symbols1 = LibrarySymbolIndex.get_symbols()
        symbols2 = LibrarySymbolIndex.get_symbols()
        assert symbols1 is symbols2  # Same frozenset object

    def test_clear_cache_resets(self):
        from sysmlpy.semantic import LibrarySymbolIndex
        LibrarySymbolIndex.clear_cache()
        symbols = LibrarySymbolIndex.get_symbols()
        assert len(symbols) > 0
