package pkg {
	constraint def AConstraint;
	constraint def AConstraint1;
	part def ABlock {
		// XPECT errors ---> "A constraint must be typed by one constraint definition." at "assert constraint two_types : AConstraint, ABlock;"
		// XPECT warnings ---> "Duplicate of inherited member name 'self' from ConstraintCheck, Part" at "assert constraint two_types : AConstraint, ABlock;"
		assert constraint two_types : AConstraint, ABlock;
		// XPECT errors ---> "A constraint must be typed by one constraint definition." at "assert constraint aConstraint0 : ABlock;"
		// XPECT warnings ---> "Duplicate of inherited member name 'self' from ConstraintCheck, Part" at "assert constraint aConstraint0: ABlock;"
		assert constraint aConstraint0: ABlock;
		//XPECT errors ---> "A constraint must be typed by one constraint definition." at "assert constraint aConstraint1 : AConstraint, AConstraint1;"
		assert constraint aConstraint1 : AConstraint, AConstraint1;
	}	
}