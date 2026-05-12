package AssignmentActionUsage_invalid {
    item i {
        attribute a;
        protected attribute b;
        private attribute c;
    }
	action def A {
        assign i.a := null;
        // XPECT errors --> "Couldn't resolve reference to Element 'b'." at "b"
        assign i.b := null;
        // XPECT errors --> "Couldn't resolve reference to Element 'c'." at "c"
        assign i.c := null;
	}
}
