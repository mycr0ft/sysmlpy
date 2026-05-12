package P {
	part def A;	
	part def B;	
	part def C;	
	part def D;	
	part def E;
	
	connection def DE {
		end : D[1];
		end : E[1];
	}
	connection def BC {
		end : B[1];
		end : C[1];
	}
	part apart : A {
		part b :B[1];
		part c: C[1];
		
		connection bc : BC connect b to c;
		connection de : DE, BC connect b to c;
		
		// XPECT errors --> "A connection must be typed by connection definitions." at "connection :A connect b to c;"
		connection :A connect b to c;
		// XPECT errors --> "A connection must be typed by connection definitions." at "connection :apart connect b to c;"
		connection :apart connect b to c;
	}
}

