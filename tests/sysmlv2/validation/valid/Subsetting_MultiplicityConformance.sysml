// XPECT noErrors ---> ""
package 'Redefinition Example' {

	part def Engine {
		part cyl : Cylinder[4..6];
	}
	part def SmallEngine :> Engine {
		part cyl1[4] :> cyl;
	}
	part def BigEngine :> Engine {
		part cyl1[6] :> cyl;
		part cyl0[0..1] :> cyl;
	}

	part def Cylinder;
	
}
