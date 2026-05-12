package 'Test' {
	package A {
		// XPECT errors --> "Must directly or indirectly specialize Parts::Part" at "part def B;"
		part def B;
		// XPECT errors --> "Features must have at least one type" at "ref f;"
		ref f;
	}
}
