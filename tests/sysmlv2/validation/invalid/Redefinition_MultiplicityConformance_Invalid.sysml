package 'Redefinition Example' {

	part def Engine {
		part cyl : Cylinder[4..6];
	}
	part def SmallEngine :> Engine {
		// XPECT warnings --> "Subsetting/redefining feature should not have larger multiplicity upper bound" at "cyl"
		part redefines cyl[7];
		//* XPECT warnings ---
 		"Redefining feature should not have smaller multiplicity lower bound" at "cyl"
		"Subsetting/redefining feature should not have larger multiplicity upper bound" at "cyl"
		--- */
		part mycyl: Cylinder[1..8] redefines cyl;
	}
	part def BigEngine :> Engine {
		// XPECT warnings --> "Redefining feature should not have smaller multiplicity lower bound" at "cyl"
		part redefines cyl[1..6];
		part bcyl: Cylinder[*];
	}

	part def Cylinder;
}
