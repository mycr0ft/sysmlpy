package ViewRendering_invalid {
	rendering r;
	
	view def V {
		render rendering r1;
		// XPECT errors ---> "A view definition may have at most one view rendering." at "render rendering r2;"
		render rendering r2;
		rendering r3;
	}

	view v {
		render r;
		// XPECT errors ---> "A view may have at most one view rendering." at "render rendering r4;"
		render rendering r4;
		// XPECT errors ---> "A view may have at most one view rendering." at "render rendering r5;"
		render rendering r5;
		rendering r6;
	}
}