package 'Redefinition Example' {
	
	part wheel : Wheel;
	// XPECT errors --> "A package-level feature cannot be redefined" at "wheel"
	part wheel1 redefines wheel;
	
	part def B {
		alias eng1 for Vehicle::eng;
	}

	part def Vehicle specializes B {
		part eng : Engine;
		// XPECT errors --> "Featuring types of redefining feature and redefined feature cannot be the same" at "eng1"
		part smallEng : Engine redefines eng1;
	}
	part def Engine {
		part cyl : Cylinder[4..6];
	}
	part def Cylinder;
	part def Wheel;
}
