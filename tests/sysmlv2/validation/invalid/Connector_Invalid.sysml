package P {
	part def A {
		part x;
	}
	part def B {
		part y {
			part z;
		}
		//* XPECT errors ---
		    "Must be an accessible feature (use dot notation for nesting)" at "A::x"
		    "Must be an accessible feature (use dot notation for nesting)" at "y::z"
		    --- */
		connect A::x to y::z;
	}
	part b {
		part y : A {
			// XPECT errors --> "Must be an accessible feature (use dot notation for nesting)" at "z"
			connect x to z;
		}
		part z;
		// XPECT errors --> "Must be an accessible feature (use dot notation for nesting)" at "y::x"
		connect y::x to z;
	}
}
