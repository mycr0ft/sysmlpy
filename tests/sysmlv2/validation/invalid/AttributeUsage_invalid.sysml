package 'ValueProperty Example' {
	port def P;
	part def A {
		part a: A;
		port p: P;
	}
	part def Vehicle {
		// XPECT errors ---> "An attribute must be typed by attribute definitions." at "attribute a : A;"
		attribute a : A;
		// XPECT errors --> "An attribute must be typed by attribute definitions." at "attribute b : A::a;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from DataValue, Part" at "attribute b : A::a;"
		attribute b : A::a;
		// XPECT errors ---> "An attribute must be typed by attribute definitions." at "attribute s : P;"
		attribute s : P;
		// XPECT errors --> "An attribute must be typed by attribute definitions." at "attribute un : A::p;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from DataValue, Port" at "attribute un : A::p;"
		attribute un: A::p;
		// XPECT errors ---> "An attribute must be typed by attribute definitions." at "attribute n: AB;"
		attribute n: AB;
	}
	connection def  AB {
		end : A;
		end : A;
	}
}
