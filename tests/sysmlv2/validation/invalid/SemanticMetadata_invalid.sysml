package SemanticMetadata_invalid {

	item def C {
		ref x;
	}
	item f : C {
		ref y;
	}

    abstract metadata def A :> Metaobjects::SemanticMetadata {
    	ref :>> baseType; // Testing that baseType can be left unbound.
    }
	
	metadata def B :> A {
		ref :>> baseType = f meta SysML::Usage;
	}
	
	item def C1 {
		// XPECT errors --> "Must have a concrete type" at "@A;"
		@A;
		// XPECT errors --> "Couldn't resolve reference to Feature 'x'." at "x"
		ref :>> x;
	}
	
	item def C2 {
		@B;
		ref :>> x;
		// XPECT errors --> "Couldn't resolve reference to Feature 'y'." at "y"
		ref :>> y;
	}
	
	item f1 {
		// XPECT errors --> "Must have a concrete type" at "@A;"
		@A;
	}
	
}
