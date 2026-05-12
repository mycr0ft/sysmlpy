package Definitions {
	part def A;
}

package Parts {
	package Definitions {
		part def A;
	}
	// XPECT linkedName at A --> Parts.Definitions.A
	part a1: Definitions::A;
	// XPECT linkedName at A --> Definitions.A
	part a2: $::Definitions::A;
	// XPECT errors --> "Couldn't resolve reference to Feature 'Parts::parts'." at "Parts::parts"  
	part a3 :> Parts::parts;
	// XPECT linkedName at parts --> Parts.parts
	part a4 :> $::Parts::parts;
}