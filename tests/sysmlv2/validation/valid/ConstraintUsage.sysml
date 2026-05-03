// XPECT noErrors ---> ""
package 'Constraint Assertions-1' {
	constraint def MassConstraint;
	part def Vehicle {
		assert constraint massConstraint : MassConstraint ;
		
		//typed by constraint definition(named ConstraintCheck)
		assert constraint massConstraint2; 
		
		//typed by constraint definition(named null)
		assert constraint {}
	}	
}
