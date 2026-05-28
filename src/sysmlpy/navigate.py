"""
sysmlpy.navigate
~~~~~~~~~~~~~~~~~

Provides the :class:`Searchable` mixin that adds typed property accessors
and ``find()`` / ``all()`` search methods to :class:`~sysmlpy.definition.Model`,
:class:`~sysmlpy.definition.Package`, and every
:class:`~sysmlpy.usage.Usage` subclass.

Usage
-----
After parsing, every node in the public-API tree supports::

    model.packages          # direct Package children
    model.parts             # direct Part children (defs + usages)
    model.actions           # direct Action children

    model.find('Focus')                    # by name, any depth
    model.find(sysml_type='action')        # by type keyword, any depth
    model.find('Focus', sysml_type='action')  # name + type
    model.find(sysml_type=Action)          # by class
    model.find('Focus', recursive=False)   # direct children only

    model.all('part')                      # shorthand for find(sysml_type='part')

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
        """Direct :class:`~sysmlpy.definition.Package` children."""
        return self._children_of_type("package")

    @property
    def parts(self):
        """Direct :class:`~sysmlpy.usage.Part` children (definitions and usages)."""
        return self._children_of_type("part")

    @property
    def items(self):
        """Direct :class:`~sysmlpy.usage.Item` children (definitions and usages)."""
        return self._children_of_type("item")

    @property
    def attributes(self):
        """Direct :class:`~sysmlpy.usage.Attribute` children (definitions and usages)."""
        return self._children_of_type("attribute")

    @property
    def ports(self):
        """Direct :class:`~sysmlpy.usage.Port` children (definitions and usages)."""
        return self._children_of_type("port")

    @property
    def actions(self):
        """Direct :class:`~sysmlpy.usage.Action` children (definitions and usages)."""
        return self._children_of_type("action")

    @property
    def states(self):
        """Direct :class:`~sysmlpy.usage.State` children (definitions and usages)."""
        return self._children_of_type("state")

    @property
    def constraints(self):
        """Direct :class:`~sysmlpy.usage.Constraint` children (definitions and usages)."""
        return self._children_of_type("constraint")

    @property
    def calculations(self):
        """Direct :class:`~sysmlpy.usage.Calculation` children (definitions and usages)."""
        return self._children_of_type("calculation")

    @property
    def requirements(self):
        """Direct :class:`~sysmlpy.usage.Requirement` children (definitions and usages)."""
        return self._children_of_type("requirement")

    @property
    def connections(self):
        """Direct :class:`~sysmlpy.usage.Connection` children (definitions and usages)."""
        return self._children_of_type("connection")

    @property
    def flows(self):
        """Direct :class:`~sysmlpy.usage.Flow` children (definitions and usages)."""
        return self._children_of_type("flow")

    @property
    def enumerations(self):
        """Direct :class:`~sysmlpy.usage.Enumeration` children."""
        return self._children_of_type("enumeration")

    @property
    def interfaces(self):
        """Direct :class:`~sysmlpy.usage.Interface` children (definitions and usages)."""
        return self._children_of_type("interface")

    @property
    def use_cases(self):
        """Direct :class:`~sysmlpy.usage.UseCase` children (definitions and usages)."""
        return self._children_of_type("use_case")

    @property
    def references(self):
        """Direct :class:`~sysmlpy.usage.Reference` children."""
        return self._children_of_type("reference")

    @property
    def messages(self):
        """Direct :class:`~sysmlpy.usage.Message` children."""
        return self._children_of_type("message")

    @property
    def allocations(self):
        """Direct :class:`~sysmlpy.usage.Allocation` children (definitions and usages)."""
        return self._children_of_type("allocation")

    @property
    def views(self):
        """Direct :class:`~sysmlpy.usage.View` children (definitions and usages)."""
        return self._children_of_type("view")

    @property
    def viewpoints(self):
        """Direct :class:`~sysmlpy.usage.Viewpoint` children (definitions and usages)."""
        return self._children_of_type("viewpoint")

    # ------------------------------------------------------------------
    # Search methods
    # ------------------------------------------------------------------

    def find(self, name=None, *, sysml_type=None, type=None, recursive=True):
        """Find model elements by name and/or SysML type.

        Parameters
        ----------
        name : str, optional
            Declared element name to match exactly.  ``None`` matches any name.
        sysml_type : str or class, optional
            SysML type to filter by.  Pass a string keyword (``'part'``,
            ``'action'``, …) or the corresponding class (``Part``,
            ``Action``, …).  ``None`` matches any type.
        type : str or class, optional
            Deprecated alias for ``sysml_type``.
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

            model.find(sysml_type='action', recursive=False)

        Find by class instead of string::

            from sysmlpy import Part
            model.find(sysml_type=Part)

        Combine name and type::

            model.find('engine', sysml_type='part')
        """
        if type is not None and sysml_type is None:
            import warnings
            warnings.warn(
                "find(type=...) is deprecated; use find(sysml_type=...) instead",
                DeprecationWarning, stacklevel=2
            )
            sysml_type = type

        results = []
        for child in getattr(self, "children", []):
            # --- name gate ---
            if name is not None and getattr(child, "name", None) != name:
                name_ok = False
            else:
                name_ok = True

            # --- type gate ---
            if sysml_type is None:
                type_ok = True
            elif isinstance(sysml_type, str):
                type_ok = getattr(child, "sysml_type", None) == sysml_type
            else:
                type_ok = isinstance(child, sysml_type)

            if name_ok and type_ok:
                results.append(child)

            # --- recurse ---
            if recursive and hasattr(child, "find"):
                results.extend(child.find(name=name, sysml_type=sysml_type, recursive=True))

        return results

    def all(self, sysml_type, type=None, recursive=True):
        """Return all elements of *sysml_type*, searching recursively by default.

        This is a convenience alias for ``find(sysml_type=sysml_type, recursive=recursive)``.

        Parameters
        ----------
        sysml_type : str or class
            SysML type string (``'part'``, ``'action'``, …) or the
            corresponding class.
        type : str or class, optional
            Deprecated alias for ``sysml_type``.
        recursive : bool
            When ``True`` (default) the search descends into every child.

        Returns
        -------
        list
        """
        if type is not None and sysml_type is None:
            import warnings
            warnings.warn(
                "all(type=...) is deprecated; use all(sysml_type=...) instead",
                DeprecationWarning, stacklevel=2
            )
            sysml_type = type
        return self.find(sysml_type=sysml_type, recursive=recursive)

    def find_one(self, name=None, *, sysml_type=None):
        """Return the single matching element, or None if not found.

        Raises LookupError if more than one match is found.
        Use find() if you expect multiple results.
        """
        results = self.find(name, sysml_type=sysml_type)
        if not results:
            return None
        if len(results) > 1:
            raise LookupError(
                f"find_one: {len(results)} matches for {name!r}, expected at most 1"
            )
        return results[0]

    # ------------------------------------------------------------------
    # Container protocol (__iter__, __len__, __contains__)
    # ------------------------------------------------------------------

    def __iter__(self):
        """Iterate over direct children."""
        return iter(self.children)

    def __len__(self) -> int:
        """Return the number of direct children."""
        return len(self.children)

    def __contains__(self, item) -> bool:
        """True if item is a direct child, or if a string matches any child's name."""
        if isinstance(item, str):
            return any(getattr(c, 'name', None) == item for c in self.children)
        return item in self.children
