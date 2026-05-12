// XPECT noErrors ---> ""
package PartUsage {
	part def A {
		part b : B;
		ref c : C; 
		part d : D;
		part e; //typed by library part def Part
		part f :> i; // also typed by part def Part
	}
	part def B;	
	part def C;
	
	item def I;
	part def D :> I { // also specializes library part def Part
		port p :> ownedPorts;
	}
	
	item i : I;
}
