"""
sysml2py.navigate
~~~~~~~~~~~~~~~~~

Provides the :class:`Searchable` mixin that adds typed property accessors
and ``find()`` / ``all()`` search methods to :class:`~sysml2py.definition.Model`,
:class:`~sysml2py.definition.Package`, and every
:class:`~sysml2py.usage.Usage` subclass.

Usage
-----
After parsing, every node in the public-API tree supports::

    model.packages          # direct Package children
    model.parts             # direct Part children (defs + usages)
    model.actions           # direct Action children

    model.find('Focus')                    # by name, any depth
    model.find(type='action')              # by type keyword, any depth
    model.find('Focus', type='action')     # name + type
    model.find(type=Action)               # by class
    model.find('Focus', recursive=False)  # direct children only

    model.all('part')                      # shorthand for find(type='part')

Type strings
------------
Each public-API class carries a ``sysml_type`` class attribute:

======================  =============
Class                   sysml_type
======================  =============
Package                 ``'package'``
Part                    ``'part'``
Item                    ``'item'``
Attribute               ``'attribute'``
Port                    ``'port'``
Action                  ``'action'``
State                   ``'state'``
Constraint              ``'constraint'``
Calculation             ``'calculation'``
Requirement             ``'requirement'``
Connection              ``'connection'``
Flow                    ``'flow'``
Enumeration             ``'enumeration'``
Interface               ``'interface'``
UseCase                 ``'use_case'``
Reference               ``'reference'``
Message                 ``'message'``
Allocation              ``'allocation'``
Metadata                ``'metadata'``
Rendering               ``'rendering'``
Individual              ``'individual'``
View                    ``'view'``
Viewpoint               ``'viewpoint'``
Concern                 ``'concern'``
Case                    ``'case'``
AnalysisCase            ``'analysis'``
VerificationCase        ``'verification'``
======================  =============
"""


class Searchable:
    """Mixin that adds typed property accessors and search helpers.

    Classes that mix this in must expose a ``children`` list whose elements
    may themselves carry a ``sysml_type`` string attribute (and optionally
    their own ``find`` method for recursive search).
    """

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _children_of_type(self, *sysml_types):
        """Return direct children whose ``sysml_type`` is in *sysml_types*."""
        return [
            c for c in getattr(self, "children", [])
            if getattr(c, "sysml_type", None) in sysml_types
        ]

    # ------------------------------------------------------------------
    # Typed property accessors (direct children only)
    # ------------------------------------------------------------------

    @property
    def packages(self):
        """Direct :class:`~sysml2py.definition.Package` children."""
        return self._children_of_type("package")

    @property
    def parts(self):
        """Direct :class:`~sysml2py.usage.Part` children (definitions and usages)."""
        return self._children_of_type("part")

    @property
    def items(self):
        """Direct :class:`~sysml2py.usage.Item` children (definitions and usages)."""
        return self._children_of_type("item")

    @property
    def attributes(self):
        """Direct :class:`~sysml2py.usage.Attribute` children (definitions and usages)."""
        return self._children_of_type("attribute")

    @property
    def ports(self):
        """Direct :class:`~sysml2py.usage.Port` children (definitions and usages)."""
        return self._children_of_type("port")

    @property
    def actions(self):
        """Direct :class:`~sysml2py.usage.Action` children (definitions and usages)."""
        return self._children_of_type("action")

    @property
    def states(self):
        """Direct :class:`~sysml2py.usage.State` children (definitions and usages)."""
        return self._children_of_type("state")

    @property
    def constraints(self):
        """Direct :class:`~sysml2py.usage.Constraint` children (definitions and usages)."""
        return self._children_of_type("constraint")

    @property
    def calculations(self):
        """Direct :class:`~sysml2py.usage.Calculation` children (definitions and usages)."""
        return self._children_of_type("calculation")

    @property
    def requirements(self):
        """Direct :class:`~sysml2py.usage.Requirement` children (definitions and usages)."""
        return self._children_of_type("requirement")

    @property
    def connections(self):
        """Direct :class:`~sysml2py.usage.Connection` children (definitions and usages)."""
        return self._children_of_type("connection")

    @property
    def flows(self):
        """Direct :class:`~sysml2py.usage.Flow` children (definitions and usages)."""
        return self._children_of_type("flow")

    @property
    def enumerations(self):
        """Direct :class:`~sysml2py.usage.Enumeration` children."""
        return self._children_of_type("enumeration")

    @property
    def interfaces(self):
        """Direct :class:`~sysml2py.usage.Interface` children (definitions and usages)."""
        return self._children_of_type("interface")

    @property
    def use_cases(self):
        """Direct :class:`~sysml2py.usage.UseCase` children (definitions and usages)."""
        return self._children_of_type("use_case")

    @property
    def references(self):
        """Direct :class:`~sysml2py.usage.Reference` children."""
        return self._children_of_type("reference")

    @property
    def messages(self):
        """Direct :class:`~sysml2py.usage.Message` children."""
        return self._children_of_type("message")

    @property
    def allocations(self):
        """Direct :class:`~sysml2py.usage.Allocation` children (definitions and usages)."""
        return self._children_of_type("allocation")

    @property
    def views(self):
        """Direct :class:`~sysml2py.usage.View` children (definitions and usages)."""
        return self._children_of_type("view")

    @property
    def viewpoints(self):
        """Direct :class:`~sysml2py.usage.Viewpoint` children (definitions and usages)."""
        return self._children_of_type("viewpoint")

    # ------------------------------------------------------------------
    # Search methods
    # ------------------------------------------------------------------

    def find(self, name=None, *, type=None, recursive=True):
        """Find model elements by name and/or SysML type.

        Parameters
        ----------
        name : str, optional
            Declared element name to match exactly.  ``None`` matches any name.
        type : str or class, optional
            SysML type to filter by.  Pass a string keyword (``'part'``,
            ``'action'``, …) or the corresponding class (``Part``,
            ``Action``, …).  ``None`` matches any type.
        recursive : bool
            When ``True`` (default) the search descends recursively into
            every child that itself exposes a ``find`` method.

        Returns
        -------
        list
            Matching elements.  Returns an empty list when nothing is found.

        Examples
        --------
        Find all elements named ``'Focus'`` anywhere in the tree::

            model.find('Focus')

        Find every action, top-level only::

            model.find(type='action', recursive=False)

        Find by class instead of string::

            from sysml2py import Part
            model.find(type=Part)

        Combine name and type::

            model.find('engine', type='part')
        """
        results = []
        for child in getattr(self, "children", []):
            # --- name gate ---
            if name is not None and getattr(child, "name", None) != name:
                name_ok = False
            else:
                name_ok = True

            # --- type gate ---
            if type is None:
                type_ok = True
            elif isinstance(type, str):
                type_ok = getattr(child, "sysml_type", None) == type
            else:
                type_ok = isinstance(child, type)

            if name_ok and type_ok:
                results.append(child)

            # --- recurse ---
            if recursive and hasattr(child, "find"):
                results.extend(child.find(name=name, type=type, recursive=True))

        return results

    def all(self, type, recursive=True):
        """Return all elements of *type*, searching recursively by default.

        This is a convenience alias for ``find(type=type, recursive=recursive)``.

        Parameters
        ----------
        type : str or class
            SysML type string (``'part'``, ``'action'``, …) or the
            corresponding class.
        recursive : bool
            When ``True`` (default) the search descends into every child.

        Returns
        -------
        list
        """
        return self.find(type=type, recursive=recursive)
