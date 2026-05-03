// XPECT noErrors ---> ""
package 'Action Example' {
	part def P;
	part def Q;
	part def R;
	
	action def A { in p : P; out q : Q; }
	action def B { in q: Q; out r : R; }
		
	action def C { in p : P; out r : R;
		bind a.p = p;
		
		action a: A { in p; out q; out part x; }
		
		succession flow a.q to b.q;
		flow from a.x to b.x;
		
		action b: B { in q; out r = C::r; in x; }
	}
	
}
