// XPECT noErrors ---> ""
package P {
	part def A;
	part def B;
	part def C;
	part def D;
	part def E;
	part def F;
	
	connection def AB {
		end : D[1];
		end : F[1];
	}
	
	part a : A {
		part b : B[1] {
			part c : C[1] {
				part cc: C[1]{
					part d : D[2];
				}			
				part d : D[2];
			}
			part e: E[1] {
				part f : F[2];
			}						
			connection : AB connect c.cc.d to e.f;		
		}
	}
	
}
