// XPECT noErrors ---> ""
package VariabilityModel {

	part def B;
	part b1 : B;
	part b2 : B;

    variation attribute def AttributeChoices {
    	variant attribute a1;
    	variant attribute a2;
    }

    variation part def PartChoices :> B {
        variant b1;
        variant b2 {
        	variation port portChoices {
        		variant port p1;
        		variant port p2;
        	}
        }
    }
    
    part def D;
    part d1 : D;
    part d2 : D;

    part c {
        variation part d : D {
        	variant d1;
        	variant d2;
        }
        
        variation part e {
        	variant part e0[0];
        	variant part e1[1];
        } 
        
        variation action f {
        	variant action f1;
        	variant action f2;
        }       
    }
    
	variation case caseChoices {
    	variant case c1;
    	variant case c2;
    }

    variation requirement r {
    	variant requirement r1;
    }

}
