package VariabilityModel {

	part def B;
	part b1 : B;
	part b2 : B;

    variation attribute def AttributeChoices {
    	variant attribute a1;
		// XPECT errors --> "An owned usage of a variation must be a variant." at "attribute a2;"
    	attribute a2;
    }

    // XPECT errors --> "A variation must not specialize another variation." at "AttributeChoices"
    variation attribute def AttributeChoices1 :> AttributeChoices;
    
    part def PartChoices :> B {
		// XPECT errors --> "A variant must be an owned member of a variation." at "variant b1;"
        variant b1;
		// XPECT errors --> "A variant must be an owned member of a variation." at "variant b2;"
        variant b2;
    }
    
    part def D;
    part d1 : D;
    part d2 : D;

    part c {
        variation part d : D {
			// XPECT errors --> "An owned usage of a variation must be a variant." at "part d1;"
        	part d1;
        	variant part d2;
        }
        
        action f {
			// XPECT errors --> "A variant must be an owned member of a variation." at "variant action f1;"
        	variant action f1;
        	action f2;
        }
        
        // XPECT errors --> "A variation must not specialize another variation." at "d"
    	variation part e :> d;
              
    }
}
