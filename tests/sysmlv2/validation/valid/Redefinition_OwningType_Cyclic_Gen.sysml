// XPECT noErrors ---> ""
package 'Redefinition Example' {
	
	part def A :> C;
	
	part def B {
		part a: A;
	}
	
	part def C :> A, B {
		part a redefines B::a;
	}

}
