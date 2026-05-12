// XPECT noErrors ---> ""
package P {
	part def A;
	part def B;
	part def C;
	part def D;
	part def E {
		part a : A[0..5];
		part b : B {
			part c : C[1] {
				part d : D[5];
			}
		}
		connect [0..1] a to [1] cd ::> b.c.d;
	}
}

