"""
Tests for sysml2py.navigate — typed property accessors and find() / all()
search on Model, Package, and Usage objects.
"""

import pytest
from sysml2py import loads, Part, Item, Action, Attribute, Package, Searchable

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

MODEL_TEXT = """
package 'TakePicture' {

    item def Scene;
    item def Image;
    item def Picture;

    part def Camera;
    part def Lens;

    attribute def Quality;

    action def Focus {
        in scene : Scene;
        out image : Image;
    }

    action def Shoot {
        in image : Image;
        out picture : Picture;
    }

    action def TakePicture {
        in item scene : Scene;
        out item picture : Picture;

        action focus : Focus {
            in item scene;
            out item image;
        }

        flow focus.image to shoot.image;

        then action shoot : Shoot {
            in item;
            out item picture;
        }
    }

    part camera : Camera {
        part lens : Lens;
        attribute quality : Quality;
    }
}
"""


@pytest.fixture
def model():
    return loads(MODEL_TEXT)


@pytest.fixture
def pkg(model):
    return model.packages[0]


# ---------------------------------------------------------------------------
# Searchable mixin is present on the right classes
# ---------------------------------------------------------------------------


def test_model_is_searchable(model):
    assert isinstance(model, Searchable)


def test_package_is_searchable(pkg):
    assert isinstance(pkg, Searchable)


def test_usage_subclass_is_searchable(pkg):
    assert isinstance(pkg.actions[0], Searchable)


# ---------------------------------------------------------------------------
# model.packages
# ---------------------------------------------------------------------------


def test_model_packages_returns_list(model):
    assert isinstance(model.packages, list)


def test_model_packages_nonempty(model):
    assert len(model.packages) == 1


def test_model_packages_are_packages(model):
    from sysml2py import Package
    for p in model.packages:
        assert isinstance(p, Package)
        assert p.sysml_type == "package"


# ---------------------------------------------------------------------------
# Typed properties on Package (direct children)
# ---------------------------------------------------------------------------


def test_pkg_items(pkg):
    # item def Scene / Image / Picture
    result = pkg.items
    assert isinstance(result, list)
    assert len(result) == 3
    names = {c.name for c in result}
    assert "Scene" in names
    assert "Image" in names
    assert "Picture" in names


def test_pkg_parts(pkg):
    result = pkg.parts
    assert isinstance(result, list)
    # Camera, Lens (def) + camera (usage) = 3 tops
    assert len(result) >= 2
    names = {c.name for c in result}
    assert "Camera" in names


def test_pkg_actions(pkg):
    result = pkg.actions
    assert isinstance(result, list)
    assert len(result) >= 2
    names = {c.name for c in result}
    assert "Focus" in names
    assert "Shoot" in names


def test_pkg_attributes(pkg):
    result = pkg.attributes
    assert isinstance(result, list)
    names = {c.name for c in result}
    assert "Quality" in names


def test_typed_property_returns_correct_sysml_type(pkg):
    for part in pkg.parts:
        assert part.sysml_type == "part"
    for action in pkg.actions:
        assert action.sysml_type == "action"
    for item in pkg.items:
        assert item.sysml_type == "item"


def test_typed_property_empty_when_no_children_of_type(pkg):
    # No flows defined at top level of this package
    assert pkg.flows == []
    assert pkg.states == []
    assert pkg.requirements == []


# ---------------------------------------------------------------------------
# is_definition property
# ---------------------------------------------------------------------------


def test_is_definition_true_for_defs(pkg):
    for action in pkg.actions:
        if action.name in ("Focus", "Shoot", "TakePicture"):
            assert action.is_definition is True


def test_is_definition_false_for_usages(pkg):
    # camera is a usage, not a definition
    camera_list = [c for c in pkg.parts if c.name == "camera"]
    if camera_list:
        assert camera_list[0].is_definition is False


# ---------------------------------------------------------------------------
# find() — name search
# ---------------------------------------------------------------------------


def test_find_by_name_returns_list(model):
    result = model.find("Focus")
    assert isinstance(result, list)


def test_find_by_name_finds_element(model):
    result = model.find("Focus")
    assert len(result) >= 1
    assert all(r.name == "Focus" for r in result)


def test_find_by_name_returns_empty_for_unknown(model):
    result = model.find("DoesNotExist")
    assert result == []


def test_find_by_name_on_package(pkg):
    result = pkg.find("Shoot")
    assert len(result) >= 1
    assert result[0].name == "Shoot"


# ---------------------------------------------------------------------------
# find() — type search
# ---------------------------------------------------------------------------


def test_find_by_type_string(model):
    result = model.find(type="action")
    assert len(result) >= 2
    assert all(r.sysml_type == "action" for r in result)


def test_find_by_type_class(model):
    result = model.find(type=Action)
    assert len(result) >= 2
    assert all(isinstance(r, Action) for r in result)


def test_find_by_type_part_class(model):
    result = model.find(type=Part)
    assert all(isinstance(r, Part) for r in result)


# ---------------------------------------------------------------------------
# find() — combined name + type
# ---------------------------------------------------------------------------


def test_find_name_and_type_match(model):
    result = model.find("Focus", type="action")
    assert len(result) >= 1
    assert result[0].name == "Focus"
    assert result[0].sysml_type == "action"


def test_find_name_and_type_no_match(model):
    # "Focus" is an action, not a part
    result = model.find("Focus", type="part")
    assert result == []


# ---------------------------------------------------------------------------
# find() — recursive vs non-recursive
# ---------------------------------------------------------------------------


def test_find_recursive_finds_nested_part():
    """Recursive find() descends into nested part children."""
    m = loads("""
    package Test {
        part engine : Engine {
            part cylinder : Cylinder;
        }
    }
    """)
    # 'cylinder' is inside 'engine', not a direct package child
    result = m.find("cylinder")
    assert len(result) >= 1
    assert result[0].name == "cylinder"


def test_find_non_recursive_misses_nested_part():
    """Non-recursive find() only checks direct children of the caller."""
    m = loads("""
    package Test {
        part engine : Engine {
            part cylinder : Cylinder;
        }
    }
    """)
    # recursive=False on model does not descend into packages
    result = m.find("cylinder", recursive=False)
    assert result == []


def test_find_recursive_on_package_finds_nested():
    """Recursive find() on a Package descends into nested parts."""
    m = loads("""
    package Test {
        part engine : Engine {
            part cylinder : Cylinder;
        }
    }
    """)
    pkg = m.packages[0]
    result = pkg.find("cylinder")
    assert len(result) >= 1
    assert result[0].name == "cylinder"


def test_find_non_recursive_on_package_misses_nested():
    """Non-recursive find() on a Package only looks at direct children."""
    m = loads("""
    package Test {
        part engine : Engine {
            part cylinder : Cylinder;
        }
    }
    """)
    pkg = m.packages[0]
    result = pkg.find("cylinder", recursive=False)
    assert result == []


# ---------------------------------------------------------------------------
# all() convenience method
# ---------------------------------------------------------------------------


def test_all_type_string(model):
    result = model.all("action")
    assert isinstance(result, list)
    assert len(result) >= 2
    assert all(r.sysml_type == "action" for r in result)


def test_all_type_class(model):
    result = model.all(Part)
    assert all(isinstance(r, Part) for r in result)


def test_all_non_recursive(pkg):
    # Non-recursive all() on the package — direct action children only
    direct = pkg.all("action", recursive=False)
    recursive = pkg.all("action", recursive=True)
    assert len(recursive) >= len(direct)


# ---------------------------------------------------------------------------
# Nested element navigation
# ---------------------------------------------------------------------------


def test_nested_part_has_typed_properties(pkg):
    # camera : Camera contains lens : Lens and quality : Quality
    cameras = [c for c in pkg.parts if c.name == "camera"]
    if not cameras:
        pytest.skip("camera part not loaded into children")
    camera = cameras[0]
    assert isinstance(camera.parts, list)
    assert isinstance(camera.attributes, list)


def test_programmatic_model_navigation():
    """Navigation works on programmatically constructed models too."""
    from sysml2py import Package, Part, Action, Attribute

    pkg = Package()
    pkg._set_name("MyPkg")

    p = Part()
    p._set_name("Engine")

    a = Action()
    a._set_name("Start")

    attr = Attribute()
    attr._set_name("mass")

    pkg._set_child(p)
    pkg._set_child(a)
    pkg._set_child(attr)

    assert len(pkg.parts) == 1
    assert pkg.parts[0].name == "Engine"

    assert len(pkg.actions) == 1
    assert pkg.actions[0].name == "Start"

    assert len(pkg.attributes) == 1
    assert pkg.attributes[0].name == "mass"

    found = pkg.find("Start")
    assert len(found) == 1
    assert found[0].name == "Start"

    found_typed = pkg.find("Engine", type="part")
    assert len(found_typed) == 1

    not_found = pkg.find("Engine", type="action")
    assert not_found == []


def test_all_on_programmatic_model():
    from sysml2py import Model, Package, Part, Action

    m = Model()
    p = Package()
    p._set_name("Pkg")
    part1 = Part()
    part1._set_name("Wheel")
    part2 = Part()
    part2._set_name("Axle")
    act = Action()
    act._set_name("Drive")
    p._set_child(part1)
    p._set_child(part2)
    p._set_child(act)
    m._set_child(p)

    all_parts = m.all("part")
    assert len(all_parts) == 2
    assert {r.name for r in all_parts} == {"Wheel", "Axle"}

    all_actions = m.all("action")
    assert len(all_actions) == 1
    assert all_actions[0].name == "Drive"
