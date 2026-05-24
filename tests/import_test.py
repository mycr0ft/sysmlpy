#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for import visibility validation and serialization.
"""

import pytest
import sysmlpy


class TestImportVisibility:
    """Tests for import visibility validation."""

    def test_import_without_visibility_raises_error(self):
        """Import without visibility keyword should raise a syntax error."""
        from sysmlpy.antlr_parser import SysMLSyntaxError
        with pytest.raises(SysMLSyntaxError):
            sysmlpy.loads("""
            package P {
                import OtherPackage::*;
            }
            """)

    def test_private_import_works(self):
        """Private import should parse successfully."""
        model = sysmlpy.loads("""
        package P {
            private import OtherPackage::*;
        }
        """)
        assert model is not None

    def test_public_import_works(self):
        """Public import should parse successfully."""
        model = sysmlpy.loads("""
        package P {
            public import OtherPackage::*;
        }
        """)
        assert model is not None

    def test_protected_import_works(self):
        """Protected import should parse successfully."""
        model = sysmlpy.loads("""
        package P {
            protected import OtherPackage::*;
        }
        """)
        assert model is not None

    def test_membership_import_without_visibility_raises_error(self):
        """Membership import without visibility should raise a syntax error."""
        from sysmlpy.antlr_parser import SysMLSyntaxError
        with pytest.raises(SysMLSyntaxError):
            sysmlpy.loads("""
            package P {
                import OtherPackage::SomeElement;
            }
            """)

    def test_membership_import_with_visibility_works(self):
        """Membership import with visibility should parse successfully."""
        model = sysmlpy.loads("""
        package P {
            private import OtherPackage::SomeElement;
        }
        """)
        assert model is not None


class TestImportRoundTrip:
    """Tests for import serialization round-trip."""

    def test_namespace_import_round_trip(self):
        """Namespace import should survive dump -> load round trip."""
        model = sysmlpy.loads("""
        package P {
            private import ScalarValues::*;
            public import BaseTypes;
            protected import ISQ;
        }
        """)

        output = model.dump()
        model2 = sysmlpy.loads(output)

        pkg = model2.children[0]
        import_count = sum(1 for c in pkg.grammar.body.children if c.__class__.__name__ == 'Import')
        assert import_count == 3

    def test_membership_import_round_trip(self):
        """Membership import should survive dump -> load round trip."""
        model = sysmlpy.loads("""
        package P {
            private import ISQ::LengthValue;
            public import BaseTypes::SomeType;
        }
        """)

        output = model.dump()
        model2 = sysmlpy.loads(output)

        pkg = model2.children[0]
        import_count = sum(1 for c in pkg.grammar.body.children if c.__class__.__name__ == 'Import')
        assert import_count == 2

    def test_visibility_preserved_in_dump(self):
        """Visibility keywords should be preserved in dump output."""
        model = sysmlpy.loads("""
        package P {
            private import A;
            public import B;
            protected import C;
        }
        """)

        output = model.dump()
        assert "private import" in output
        assert "public import" in output
        assert "protected import" in output


class TestAddImport:
    """Tests for the Package.add_import() method."""

    def test_add_private_import(self):
        """Adding a private import should work."""
        model = sysmlpy.loads("package P { part def X; }")
        pkg = model.children[0]

        pkg.add_import('ScalarValues', visibility='private')
        output = model.dump()

        assert "private import" in output

    def test_add_public_import(self):
        """Adding a public import should work."""
        model = sysmlpy.loads("package P { part def X; }")
        pkg = model.children[0]

        pkg.add_import('BaseTypes', visibility='public')
        output = model.dump()

        assert "public import" in output

    def test_add_protected_import(self):
        """Adding a protected import should work."""
        model = sysmlpy.loads("package P { part def X; }")
        pkg = model.children[0]

        pkg.add_import('ISQ', visibility='protected')
        output = model.dump()

        assert "protected import" in output

    def test_add_import_invalid_visibility(self):
        """Adding an import with invalid visibility should fail."""
        model = sysmlpy.loads("package P { part def X; }")
        pkg = model.children[0]

        with pytest.raises(ValueError, match="visibility must be"):
            pkg.add_import('ScalarValues', visibility='invalid')

    def test_add_membership_import(self):
        """Adding a membership import should work."""
        model = sysmlpy.loads("package P { part def X; }")
        pkg = model.children[0]

        pkg.add_import('ISQ', visibility='private', membership='LengthValue')
        output = model.dump()

        assert "private import ISQ::LengthValue" in output

    def test_add_import_round_trip(self):
        """Programmatically added imports should survive round trip."""
        model = sysmlpy.loads("package P { part def X; }")
        pkg = model.children[0]

        pkg.add_import('ScalarValues', visibility='private')
        pkg.add_import('BaseTypes', visibility='public')
        pkg.add_import('ISQ', visibility='protected', membership='LengthValue')

        output = model.dump()
        model2 = sysmlpy.loads(output)

        pkg2 = model2.children[0]
        import_count = sum(1 for c in pkg2.grammar.body.children if c.__class__.__name__ == 'Import')
        assert import_count == 3

    def test_add_import_chaining(self):
        """add_import should return self for chaining."""
        model = sysmlpy.loads("package P { part def X; }")
        pkg = model.children[0]

        result = pkg.add_import('A', visibility='private').add_import('B', visibility='public')
        assert result is pkg
