package Test {
	attribute def T;
	
	calc def C { return T; }
	
	calc def C1 {
		return r1 : T;
		// XPECT errors --> "Only one return parameter is allowed" at "return r2 : T;"
		return r2 : T;
	}
	
	calc c : C { return T; }
	
	calc c2 : C {
		return r1 : T;
		// XPECT errors --> "Only one return parameter is allowed" at "return r2 : T;"
		return r2 : T;
	}
}