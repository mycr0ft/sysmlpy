import json

import pytest

from sysmlpy import Interface, loads, to_interchange, from_interchange


class TestInterfaceEnds:
    """Interface ends parsed into .ends / .iface_connections."""

    SOURCE = """package P {
    part def W { port waterOut; }
    part def R { port inn; }
    interface def Supply {
        end supplierPort;
        end consumerPort;
    }
    part def M {
        part w : W; part r : R;
        interface waterLine : Supply {
            end supplierPort ::> w.waterOut;
            end consumerPort ::> r.inn;
        }
    }
}"""

    def test_usage_ends_parsed(self):
        m = loads(self.SOURCE)
        mch = next(c for c in m.children[0].children if c.name == 'M')
        iface = next(c for c in mch.children if type(c).__name__ == 'Interface')
        assert [e[0] for e in iface.ends] == ['supplierPort', 'consumerPort']

    def test_ref_targets_captured(self):
        m = loads(self.SOURCE)
        mch = next(c for c in m.children[0].children if c.name == 'M')
        iface = next(c for c in mch.children if type(c).__name__ == 'Interface')
        assert iface.iface_connections == [
            ('supplierPort', 'w.waterOut'),
            ('consumerPort', 'r.inn'),
        ]

    def test_def_ends_parsed(self):
        m = loads(self.SOURCE)
        sup = next(c for c in m.children[0].children
                   if getattr(c, 'name', '') == 'Supply')
        assert [e[0] for e in sup.ends] == ['supplierPort', 'consumerPort']

    def test_ends_survive_dump_round_trip(self):
        from sysmlpy.formatting import classtree
        d = loads(self.SOURCE)
        dumped = classtree(d).dump()
        m2 = loads(dumped)
        mch = next(c for c in m2.children[0].children if c.name == 'M')
        iface2 = next(c for c in mch.children
                      if type(c).__name__ == 'Interface')
        assert [e[0] for e in iface2.ends] == ['supplierPort', 'consumerPort']

    def test_iv_renders_interface_shape(self):
        from sysmlpy import as_interconnection_view
        view = as_interconnection_view(loads(self.SOURCE))
        assert 'rectangle "waterLine" as' in view
