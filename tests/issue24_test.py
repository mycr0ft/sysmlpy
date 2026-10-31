"""Issue #24 (CARTA downstream report): metadata applications on the model.

Three notations, three layers:

* ``metadata m : M about X, W;`` — the type survived
  (``typed_by_name == 'M'``), but ``about`` targets and metadata-body values
  did not reach the element.  The grammar's ``MetadataFeature.annotations``
  holds the ``Annotation`` list (dict key ``ownedRelationship_about``) and
  ``bodyFeatures`` are raw dicts with ``name``/``value``/``text`` — both are
  now read in ``_metadata_from_feature``.
* ``part def X { @M { w = 1; } }`` — the visitor emitted the complete
  ``AnnotatingElement → MetadataFeature``; the definition-body dispatch
  dropped it.  It now attaches to the **owning element**
  (``element.annotations``), never uuid-named.
* ``#M part def Y;`` — the visitor emitted nothing (``PrefixMetadataMember``
  sat inside the occurrence prefix); captured into ``prefixMetadata``,
  carried by both occurrence prefix grammar classes, attached like ``@``, and
  re-emitted as ``#M`` on dump.

Serializer defects fixed along the way (dump was lossy, so annotations were
read-only): ``@M { … }`` dumped as ``@ : M {a=1;};`` — the ``:`` belongs
between a declared name and its type only, and a braced ``{ … }`` metadata
body carries NO terminator; ``metadata m : M about X;`` dumped ``…about
X;;`` (double terminator); ``#M part def Y;`` lost the prefix entirely.
"""

from sysmlpy import loads


def test_issue24_metadata_about_and_type():
    model = loads("package P { metadata def M; part def X; part def W; "
                  "metadata m1 : M about X, W; }")
    pkg = model.children[0]
    m1 = [c for c in pkg.children if getattr(c, "name", None) == "m1"][0]
    assert m1.type_name == "M"
    assert m1.annotated == ["X", "W"], m1.annotated
    names = [type(e).__name__ + ":" + e.name for e in m1.annotated_elements]
    assert "Part:X" in names
    assert m1.values == {}


def test_issue24_metadata_values_read_from_body():
    model = loads("""package P {
      metadata def M;
      part def X { @M { w = 1; note = 'planning'; } }
    }""")
    x = model.find_one("X")
    assert len(x.annotations) == 1
    md = x.annotations[0]
    assert md.type_name == "M"
    # values stay as written (string literals keep their quotes) — this is
    # the "values are textual" rule from the plan
    assert md.values == {"w": "1", "note": "'planning'"}, md.values
    assert md.value_text == {"w": "=1", "note": "='planning'"}


def test_issue24_at_annotations_attached_to_owning_element():
    model = loads("""package P {
      metadata def M;
      metadata def W;
      part def X { @M { w = 1; } @W { z = 'two'; } }
    }""")
    x = model.find_one("X")
    assert [(a.type_name, a.values) for a in x.annotations] == [
        ("M", {"w": "1"}), ("W", {"z": "'two'"})]
    # annotations are not members — they do not enter the element's children
    assert not [c for c in x.children if type(c).__name__ == "Metadata"]


def test_issue24_hash_prefix_annotation():
    model = loads("package P { metadata def M; #M part def Y; #M part y; }")
    for name in ("Y", "y"):
        el = model.find_one(name)
        assert [a.type_name for a in el.annotations] == ["M"], (name, el.annotations)


def test_issue24_requirement_prefix_annotation():
    model = loads("package P { metadata def M; #M requirement def R; }")
    r = model.children[0].children[-1]
    assert [a.type_name for a in r.annotations] == ["M"], r.annotations


def test_issue24_dump_notation_and_round_trip():
    import sysmlpy
    model = loads("package P { metadata def M; metadata def W; "
                  "part def X { @M { w = 1; } @W { z = 'two'; } } "
                  "metadata m1 : M about X, W; }")
    dump = model.dump()
    # `about` keeps the declared-metadata keyword shape, no double terminator
    assert "@ m1 : M about X, W;" in dump, dump
    # the bare `@M` form keeps no fake colon
    assert "@ M {w=1;}" in dump or "@M {w=1;}" in dump, dump
    again = sysmlpy.loads(dump)
    assert str(again).strip() == dump.strip()
    # and the annotation survives the round trip
    x2 = again.find_one("X")
    assert [(a.type_name, a.values) for a in x2.annotations] == [
        ("M", {"w": "1"}), ("W", {"z": "'two'"})]


def test_issue24_hash_prefix_dump_round_trip():
    import sysmlpy
    model = loads("package P { metadata def M; #M part def Y; }")
    dump = model.dump()
    assert "#M part def Y;" in dump, dump
    again = sysmlpy.loads(dump)
    assert str(again).strip() == dump.strip()
    assert [a.type_name for a in again.find_one("Y").annotations] == ["M"]