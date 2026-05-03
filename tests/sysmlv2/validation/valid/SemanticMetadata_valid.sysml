// XPECT noErrors ---> ""
package SemanticMetadata_valid {
	public import Metaobjects::SemanticMetadata;

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
	
	#B def C1 {
		ref :>> x;
	}
	
	#B f1 {
		ref :>> x;
		ref :>> y;
	}
	
    requirement def G;
	requirement gs : G[*] nonunique;
	metadata def g :> SemanticMetadata {
	    :>> baseType = gs meta SysML::RequirementUsage;
	}
	
	requirement r1;
	#g requirement r2 {
		subject;
		actor #B a;
		assume #g constraint b;
		require #g r1;
	}
}
