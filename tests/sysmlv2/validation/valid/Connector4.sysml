// XPECT noErrors ---> ""
package P {
	
	part def A {
		part b1: B;
		part b2: B;
	}
	
	part def B {
		part c: C;
		part e: E;
	}
	
	part def C {
		part d: D;
	}
	
	part def D;
	
	part def E {
		part f: F;
	}
	
	part def F;
	
	connection def AB {
		end : D[1];
		end : F[1];
	}
	
	part a : A {
		connection : AB connect b1.c.d to b2.e.f;	
	}
	
}
