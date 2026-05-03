package P {
	part def P;	
	part def B;	
	part def C;	
	
	connection def BC1 {
		end : B[1];
		end : C[1];
	}
	allocation def BC2 {
		end : B[1];
		end : C[1];
	}
	part p : P {
		part b : B[1];
		part c: C[1];
		
		allocation bc : BC2 allocate b to c;
		
		// XPECT errors --> "An allocation must be typed by allocation definitions." at "allocation :P allocate b to c;"
		allocation :P allocate b to c;
		// XPECT errors --> "An allocation must be typed by allocation definitions." at "allocation :p allocate b to c;"
		allocation :p allocate b to c;
		// XPECT errors --> "An allocation must be typed by allocation definitions." at "allocation :BC1 allocate b to c;"
		allocation :BC1 allocate b to c;
	}
}

