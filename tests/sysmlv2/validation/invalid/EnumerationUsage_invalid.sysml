package EnumerationUsage_invalid {
	attribute def A;
	enum def E {a; b; c;}
	enum def EE;
	
	attribute a1 : E;
	// XPECT errors --> "An enumeration attribute cannot have more than one type." at "attribute a2 : E, A;"
	attribute a2 : E, A;
	// XPECT errors --> "An enumeration attribute cannot have more than one type." at "attribute a3 : E, EE;"
	attribute a3 : E, EE;
	
	enum e1 : E;
	// XPECT errors ---> "An enumeration must be typed by one enumeration definition." at "enum e2 : A;"
	enum e2 : A;
	// XPECT errors --> "An enumeration must be typed by one enumeration definition." at "enum e3 : E, EE;"
	enum e3 : E, EE;
}
